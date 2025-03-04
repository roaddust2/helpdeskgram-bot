import os
from dotenv import load_dotenv


load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
DEFAULT_LOCALE = os.getenv("DEFAULT_LOCALE")
DEBUG = os.getenv("DEBUG", False).lower() in ("true", "1", "yes")

JIRA_HOME = os.getenv("JIRA_HOME")
JIRA_USERNAME = os.getenv("JIRA_USERNAME")
JIRA_PASSWORD = os.getenv("JIRA_PASSWORD")
JIRA_PROJECT = os.getenv("JIRA_PROJECT")
JIRA_ISSUE_TYPE = os.getenv("JIRA_ISSUE_TYPE")
