import os
from dotenv import load_dotenv
from aiogram import Bot
from aiogram.client.default import DefaultBotProperties


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
