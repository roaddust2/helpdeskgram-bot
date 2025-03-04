from settings import DEFAULT_LOCALE, DEBUG
from settings import bot
from settings import BASE_WEBHOOK_URL, WEB_SERVER_HOST, WEB_SERVER_PORT, WEBHOOK_PATH, JIRA_WEBHOOK_PATH
from app.utils import WORKDIR
import logging
import sqlite3
from app.handlers import create_issue, start
from app.api.jira_route_handler import jira_issue_update
from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import I18n, ConstI18nMiddleware, SimpleI18nMiddleware
from aiohttp import web
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application


async def on_startup(bot: Bot) -> None:
    """Set webhook"""
    await bot.set_webhook(f"{BASE_WEBHOOK_URL}{WEBHOOK_PATH}")


async def on_shutdown(bot: Bot) -> None:
    """Clean webhook"""
    await bot.delete_webhook(drop_pending_updates=True)
    await bot.session.close()


def main() -> None:

    dp = Dispatcher()

    # i18n Internationalization settings
    if DEFAULT_LOCALE:
        # TODO: Use rewrited I18nMiddleware instead, SimpleI18nMiddleware is buggy
        i18n = I18n(path=WORKDIR / 'locales', default_locale=DEFAULT_LOCALE, domain="messages")
        dp.update.middleware(SimpleI18nMiddleware(i18n=i18n))
    else:
        dp.update.middleware(ConstI18nMiddleware(locale="en"))

    # Registering routers and middlewares
    dp.include_routers(start.router, create_issue.router)
    dp.startup.register(on_startup)
    dp.shutdown.register(on_shutdown)

    # Create aiohttp web instance
    app = web.Application()
    app.router.add_post(JIRA_WEBHOOK_PATH, jira_issue_update)

    # Create webhook handler
    webhook_requests_handler = SimpleRequestHandler(dispatcher=dp, bot=bot)
    webhook_requests_handler.register(app, path=WEBHOOK_PATH)

    # Mount dispatcher startup and shutdown hooks to aiohttp application
    setup_application(app, dp, bot=bot)

    # Database setup
    DB_FILE = "db.sqlite3"
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        issue_key TEXT,
        created_at TEXT NOT NULL
    )''')
    conn.commit()
    conn.close()

    # Start web server
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":

    # Add logging
    match DEBUG:
        case True:
            logging.basicConfig(level=logging.DEBUG)
        case False:
            logging.basicConfig(level=logging.INFO)
    main()
