from __future__ import annotations
import asyncio, logging
from telegram.ext import ApplicationBuilder, CommandHandler
from telegram.constants import ParseMode
from telegram import InlineKeyboardButton, InlineKeyboardMarkup

from .config import (
    TELEGRAM_BOT_TOKEN,
    TELEGRAM_CHANNEL_ID,
    NEWS_FEED_URL,
    SCRAPE_INTERVAL_SECONDS,
    SCRAPE_MODE,
)
from . import db
from .scraper import fetch_from_rss, fetch_from_html
from .openai_helper import summarize

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s"
)
log = logging.getLogger("newsbot")


# ========== Постинг одной новости ==========
async def _post_item(application, item: dict):
    title = item['title']
    url = item['url']
    summary = item.get("summary", "")

    # Если есть картинка
    image = item.get("image")

    # Кнопка "Читать подробнее"
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("📖 Читать подробнее", url=url)]
    ])

    # Формируем текст
    text = f"<b>{title}</b>\n\n{summary}"

    try:
        if image:
            await application.bot.send_photo(
                chat_id=TELEGRAM_CHANNEL_ID,
                photo=image,
                caption=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
        else:
            await application.bot.send_message(
                chat_id=TELEGRAM_CHANNEL_ID,
                text=text,
                parse_mode=ParseMode.HTML,
                reply_markup=keyboard
            )
    except Exception as e:
        log.error(f"Ошибка при отправке поста: {e}")


# ========== Парсинг и публикация ==========
async def scrape_and_post(application):
    log.info("Scraping...")
    if not NEWS_FEED_URL:
        log.warning("NEWS_FEED_URL not configured; skip")
        return

    # Получаем список новостей
    if SCRAPE_MODE.lower() == "html":
        items = fetch_from_html(
            NEWS_FEED_URL,
            item_selector="article",
            title_selector="h2",
            link_selector="a",
        )
    else:
        items = fetch_from_rss(NEWS_FEED_URL)

    # Берём только новые
    fresh = [it for it in items if not db.seen(it["id"])]
    if not fresh:
        log.info("No new items")
        return

    # Ограничиваем максимум 5 за раз
    fresh = fresh[:2]

    # От новых к старым
    for it in reversed(fresh):
        await _post_item(application, it)
        db.mark_seen(it["id"], it["url"], it["title"], it.get("published"))
        await asyncio.sleep(2)

    log.info("Posted %d new items", len(fresh))


# ========== Команды ==========
async def cmd_start(update, context):
    await update.message.reply_text(
        "Бот активен ✅\n\n"
        "Команды:\n"
        "/latest — собрать и опубликовать свежие новости"
    )


async def cmd_latest(update, context):
    await update.message.reply_text("Собираю свежие новости...")
    await scrape_and_post(context.application)
    await update.message.reply_text("Готово ✅")


# ========== Запуск ==========
async def run():
    if not TELEGRAM_BOT_TOKEN:
        raise RuntimeError("TELEGRAM_BOT_TOKEN is empty")

    db.init_db()
    app = ApplicationBuilder().token(TELEGRAM_BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", cmd_start))
    app.add_handler(CommandHandler("latest", cmd_latest))

    # Автопостинг раз в 10 минут
    app.job_queue.run_repeating(
        lambda ctx: scrape_and_post(ctx.application),
        interval=SCRAPE_INTERVAL_SECONDS or 600,
        first=5,
    )

    await app.initialize()
    await app.start()

    try:
        await asyncio.Event().wait()
    finally:
        await app.stop()
        await app.shutdown()
