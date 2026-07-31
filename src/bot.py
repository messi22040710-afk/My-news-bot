import os
import feedparser
import logging
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# === ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ ===
TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
RSS_URL = os.environ.get("NEWS_FEED_URL")
INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_SECONDS", 3600))
AI_API_KEY = os.environ.get("OPENROUTER_API_KEY")

# === ФУНКЦИЯ ДЛЯ РЕРАЙТА НОВОСТИ ===
def rewrite_news(title, link):
    """Отправляет заголовок в ИИ и получает уникальный текст"""
    if not AI_API_KEY:
        logger.warning("⚠️ OPENROUTER_API_KEY не задан. Публикую заголовок + ссылку.")
        return f"📰 {title}\n\n🔗 Подробнее: {link}"
    
    try:
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {AI_API_KEY}",
            "Content-Type": "application/json"
        }
        prompt = f"Перепиши эту новость своим языком, как для Telegram-канала. Напиши кратко, интересно, без воды. Сохрани суть. Название: {title}. Ссылка: {link}"
        data = {
            "model": "deepseek/deepseek-r1-0528-qwen3-8b:free",  # Бесплатная мощная модель
            "messages": [{"role": "user", "content": prompt}],
            "max_tokens": 300,
            "temperature": 0.7
        }
        response = requests.post(url, headers=headers, json=data, timeout=30)
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except Exception as e:
        logger.error(f"❌ Ошибка ИИ: {e}")
        return f"📰 {title}\n\n🔗 Подробнее: {link}"

# === ФУНКЦИЯ ПОЛУЧЕНИЯ НОВОСТИ ===
def get_latest_news():
    """Возвращает первую новость из RSS-ленты"""
    if not RSS_URL:
        return None, "❌ RSS_URL не задан"

    try:
        feed = feedparser.parse(RSS_URL)
        if not feed.entries:
            return None, "❌ RSS-лента пуста"

        entry = feed.entries[0]
        title = entry.get('title', 'Без заголовка')
        link = entry.get('link', '#')

        # Переписываем новость через ИИ
        rewritten_text = rewrite_news(title, link)
        return rewritten_text, None

    except Exception as e:
        logger.error(f"❌ Ошибка парсинга RSS: {e}")
        return None, f"❌ Ошибка: {e}"

# === КОМАНДА /LATEST ===
async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить последнюю новость вручную"""
    logger.info("📩 Команда /latest")
    message, error = get_latest_news()
    if error:
        await update.message.reply_text(f"❌ {error}")
        return

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        await update.message.reply_text("✅ Новость опубликована!")
        logger.info("✅ Новость опубликована по команде /latest")
    except Exception as e:
        await update.message.reply_text(f"❌ Ошибка отправки: {e}")

# === АВТОМАТИЧЕСКАЯ ПУБЛИКАЦИЯ ===
async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Публикует новость по расписанию"""
    logger.info("⏰ Запуск автопубликации...")
    message, error = get_latest_news()
    if error:
        logger.error(f"Ошибка автопубликации: {error}")
        return

    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        logger.info("✅ Новость опубликована автоматически")
    except Exception as e:
        logger.error(f"❌ Ошибка автопубликации: {e}")

# === КОМАНДА /START ===
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 Бот с ИИ-обработкой новостей!\n\n"
        "Команды:\n"
        "/latest - опубликовать последнюю новость\n\n"
        "Бот сам переписывает новости своим языком."
    )

# === ЗАПУСК ===
def main():
    if not TOKEN or not CHANNEL_ID:
        logger.error("❌ Не заданы TOKEN или CHANNEL_ID")
        return

    logger.info("🚀 Запуск бота...")
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("latest", cmd_latest))

    if app.job_queue:
        app.job_queue.run_repeating(scheduled_post, interval=INTERVAL, first=10)
        logger.info(f"⏰ Автопубликация: раз в {INTERVAL} сек")

    app.run_polling()

if __name__ == "__main__":
    main()
