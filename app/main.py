from settings import BOT_TOKEN, DEFAULT_LOCALE, DEBUG
from app.utils import WORKDIR
import logging
import sqlite3
from app.handlers import create_issue, start
from aiogram import Bot, Dispatcher, Router, F
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.i18n import I18n, ConstI18nMiddleware, SimpleI18nMiddleware


def main() -> None:

    # Initiation
    bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))
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
    router = Router()
    router.my_chat_member.filter(F.chat.type == "private")
    router.message.filter(F.chat.type == "private")

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

    dp.run_polling(bot)


if __name__ == "__main__":

    # Add logging
    match DEBUG:
        case True:
            logging.basicConfig(level=logging.DEBUG)
        case False:
            logging.basicConfig(level=logging.INFO)
    main()
