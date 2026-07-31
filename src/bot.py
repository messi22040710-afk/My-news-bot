import os
import feedparser
import logging
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

# Проверка наличия переменных
if not TOKEN:
    logger.error("❌ TELEGRAM_BOT_TOKEN не задан!")
if not CHANNEL_ID:
    logger.error("❌ TELEGRAM_CHANNEL_ID не задан!")
if not RSS_URL:
    logger.error("❌ NEWS_FEED_URL не задан!")

# === ФУНКЦИЯ ПОЛУЧЕНИЯ НОВОСТИ ===
def get_latest_news():
    """Возвращает первую новость из RSS-ленты"""
    if not RSS_URL:
        return None, "❌ RSS_URL не задан"

    try:
        feed = feedparser.parse(RSS_URL)
        
        # Проверяем статус загрузки
        if feed.bozo:
            logger.warning(f"⚠️ Ошибка парсинга RSS: {feed.bozo_exception}")

        if not feed.entries:
            logger.warning("⚠️ RSS-лента пуста")
            return None, "❌ RSS-лента пуста"

        entry = feed.entries[0]
        title = entry.get('title', 'Без заголовка')
        link = entry.get('link', '#')

        # Формируем сообщение
        message = f"📰 {title}\n\n🔗 Подробнее: {link}"
        return message, None

    except Exception as e:
        logger.error(f"❌ Ошибка при парсинге RSS: {e}")
        return None, f"❌ Ошибка: {e}"

# === КОМАНДА /LATEST ===
async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить последнюю новость вручную"""
    # Проверяем, что команда вызвана в канале или личке
    chat_id = update.effective_chat.id
    logger.info(f"📩 Команда /latest от {chat_id}")

    message, error = get_latest_news()
    if error:
        await update.message.reply_text(f"❌ Ошибка: {error}")
        logger.error(f"Ошибка в /latest: {error}")
        return

    # Отправляем в канал
    try:
        await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
        await update.message.reply_text("✅ Новость опубликована!")
        logger.info("✅ Новость опубликована по команде /latest")
    except Exception as e:
        await update.message.reply_text(f"❌ Не удалось отправить в канал: {e}")
        logger.error(f"❌ Ошибка отправки в канал: {e}")

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
    """Приветственное сообщение"""
    await update.message.reply_text(
        "📰 Бот для публикации новостей запущен!\n\n"
        "Команды:\n"
        "/latest - опубликовать последнюю новость\n\n"
        "Бот также будет публиковать новости автоматически."
    )

# === ЗАПУСК БОТА ===
def main():
    if not TOKEN or not CHANNEL_ID:
        logger.error("❌ Ошибка: не заданы обязательные переменные TOKEN или CHANNEL_ID")
        return

    logger.info("🚀 Запуск бота...")
    app = Application.builder().token(TOKEN).build()

    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("latest", cmd_latest))

    # Настраиваем автопубликацию
    if app.job_queue:
        app.job_queue.run_repeating(scheduled_post, interval=INTERVAL, first=10)
        logger.info(f"⏰ Автопубликация настроена: раз в {INTERVAL} секунд")
    else:
        logger.warning("⚠️ JobQueue не инициализирован")

    # Запускаем бота
    app.run_polling()

if __name__ == "__main__":
    main()
