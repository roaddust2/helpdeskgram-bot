import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties
from app.utils import WORKDIR
from aiogram.utils.i18n import I18n

load_dotenv()

# Main config
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE")
DEBUG = os.getenv("DEBUG", False).lower() in ("true", "1", "yes")
bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode='HTML'))

# Jira settings
JIRA_HOME = os.getenv("JIRA_HOME")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")
JIRA_PROJECT = os.getenv("JIRA_PROJECT")
JIRA_ISSUE_TYPE = os.getenv("JIRA_ISSUE_TYPE")

# Webserver settings
BASE_WEBHOOK_URL = os.getenv("BASE_WEBHOOK_URL")
WEB_SERVER_HOST = "127.0.0.1"
WEB_SERVER_PORT = 8080
WEBHOOK_PATH = "/webhook"
JIRA_WEBHOOK_PATH = "/jira/{issue_key}"


# I18n
i18n = I18n(path=WORKDIR / 'locales', default_locale=DEFAULT_LOCALE, domain="messages")

# Categories
# When creating issue user should choose a category, rewrite if needed

CATEGORIES = [
    ("Dealer's calculator", "dealer_calc"),
    ("Client's calculator", "client_calc"),
    ("Tracking", "tracking"),
    ("Translations", "translations"),
    ("Mobile", "mobile"),
    ("Other", "other")
]


# Jira statuses, checks when webhook comes

class JiraStatuses():
    APPOINTED = "Selected for Development"
    IN_PROGRESS = "In Progress"
    DONE = "Done"
