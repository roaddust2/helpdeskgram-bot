import logging
import sqlite3
from settings import bot, i18n
from settings import DEFAULT_LOCALE, DEBUG
from settings import BASE_WEBHOOK_URL, WEB_SERVER_HOST, WEB_SERVER_PORT, WEBHOOK_PATH, JIRA_WEBHOOK_PATH
from app.handlers import commands, create_issue
from app.api.jira_route_handler import jira_issue_update
from aiogram import Bot, Dispatcher
from aiogram.utils.i18n import ConstI18nMiddleware, SimpleI18nMiddleware
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
    """Main function"""

    dp = Dispatcher()

    # i18n Internationalization settings (i18n instance is in settings)
    if DEFAULT_LOCALE:
        # TODO: Use rewrited I18nMiddleware instead, SimpleI18nMiddleware is buggy
        dp.update.middleware(SimpleI18nMiddleware(i18n=i18n))
    else:
        dp.update.middleware(ConstI18nMiddleware(locale="en"))

    # Registering routers and middlewares
    dp.include_routers(commands.router, create_issue.router)
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
    DB_FILE = "helpdeskgram.db"
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    conn.execute('pragma foreign_keys=on')
    cursor = conn.cursor()
    cursor.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        chat_id INTEGER,
        first_name TEXT,
        phone_number TEXT,
        locale TEXT,
        created_at TEXT NOT NULL
    )''')
    cursor.execute('''CREATE TABLE IF NOT EXISTS issues (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        issue_key TEXT,
        status TEXT,
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )''')
    cursor.execute('''CREATE INDEX IF NOT EXISTS idx_user_id ON issues(user_id)''')
    conn.commit()
    conn.close()

    # Start web server
    web.run_app(app, host=WEB_SERVER_HOST, port=WEB_SERVER_PORT)


if __name__ == "__main__":

    # Add logging
    log_format = "%(asctime)s - %(levelname)s - %(message)s"
    log_filename = "debug.log"

    match DEBUG:
        case True:
            logging.basicConfig(
                level=logging.DEBUG,
                format=log_format,
                handlers=[
                    logging.FileHandler(log_filename, mode='a'),
                    logging.StreamHandler()
                ]
            )
        case False:
            logging.basicConfig(level=logging.INFO)
    main()
