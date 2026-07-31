import os
import feedparser
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# === НАСТРОЙКИ ИЗ ПЕРЕМЕННЫХ ОКРУЖЕНИЯ ===
BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.environ.get("TELEGRAM_CHANNEL_ID")
RSS_URL = os.environ.get("NEWS_FEED_URL")
INTERVAL = int(os.environ.get("SCRAPE_INTERVAL_SECONDS", 3600))

# === ФУНКЦИЯ ПОСТИНГА ===
async def scheduled_post(context: ContextTypes.DEFAULT_TYPE):
    """Парсит RSS и отправляет новость в канал"""
    try:
        feed = feedparser.parse(RSS_URL)
        if feed.entries:
            entry = feed.entries[0]
            title = entry.title
            link = entry.link
            # Формируем пост
            message = f"📰 {title}\n\n🔗 {link}"
            await context.bot.send_message(chat_id=CHANNEL_ID, text=message)
    except Exception as e:
        print(f"Ошибка при публикации: {e}")

# === КОМАНДА /LATEST ===
async def cmd_latest(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отправить последнюю новость вручную"""
    await scheduled_post(context)

# === КОМАНДА /START ===
async def cmd_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📰 Бот для публикации новостей запущен!\n"
        "Он будет автоматически постить новости в канал."
    )

# === ЗАПУСК БОТА ===
async def run():
    app = Application.builder().token(BOT_TOKEN).build()

    # Добавляем обработчики команд
    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("latest", cmd_latest))

    # Инициализируем и запускаем JobQueue
    if app.job_queue:
        # Публикуем каждые INTERVAL секунд
        app.job_queue.run_repeating(scheduled_post, interval=INTERVAL, first=10)
    else:
        print("⚠️ JobQueue не инициализирован. Планировщик не работает.")

    # Запускаем бота
    await app.run_polling()

# Точка входа
if __name__ == "__main__":
    asyncio.run(run())
