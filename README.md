![Python](https://img.shields.io/badge/python-v3.10-blue)

# Telegram Helpdesk Bot for Jira  

This bot is built with **Python 3.10** and the [**Aiogram 3**](https://github.com/aiogram/aiogram) framework. 
It provides a simple helpdesk workflow through a Telegram bot and seamlessly integrates with **Jira Server**.  

## Why?  

The goal was straightforward: **receive issues via Telegram and automate their creation and updates in Jira**. 
However, after researching existing solutions, I found none that fully met my needs.  

- Some were **proprietary** and overloaded with unnecessary features.  
- Others focused on **live chat** (such as the excellent [Telegram Support Bot](https://github.com/bostrot/telegram-support-bot)).  

Since no existing tool fit my use case, I decided to build my own.  

If you find this bot useful, feel free to contribute—**pull requests are welcome!**


## Workflow

```mermaid
sequenceDiagram
    participant User
    participant TelegramBot
    participant JiraAPI
    participant JiraWebhook
    participant SupportTeam

    User->>TelegramBot: Create issue request (category, description, screenshots, contact)
    TelegramBot->>JiraAPI: Create issue with user info
    JiraAPI-->>TelegramBot: Issue created (Issue Key)

    loop Status update
        SupportTeam->>JiraWebhook: Change issue status (Selected for Dev / In Progress)
        JiraWebhook->>TelegramBot: Issue status changed
        TelegramBot-->>User: Notify about status update
    end

    SupportTeam->>JiraWebhook: Change issue status (Done)
    JiraWebhook->>TelegramBot: Issue moved to Done
    TelegramBot->>JiraAPI: Get last comment from issue
    JiraAPI->>TelegramBot: Last comment from issue
    TelegramBot-->>User: Notify about completion with last comment
```

## Features

- [Basic logic] Ask the user about problems, gather info (Category, Description, Screenshots, Contact information)
- [Basic logic] Creates issues with Jira REST API
- [Basic logic] Notifies user about issue status updates with Jira webhooks
- [Basic logic] Deliver the last issue comment with Jira REST API, when the issue updates to "Done" status
- Full i18n support EN/RU (language will be detected automatically, which is not good tbh)
- The user can list all his issues that currently are not in "Done" status 

## Setup

1. Clone repo
2. Input your Telegram Bot token and Jira credentials listed in example.env
3. Bot is in webhook mode, so you will need a domain, vscode ports works pretty good for development reasons. I use Let's Encrypt certificates and actual domain
4. Create a webhook on issues update in Jira admin settings
5. Configure settings.py in the root folder to your needs
6. ```bash make setup```
9. ```bash make start```
10. Bot uses sqlite database, so there is no need in database setup/migrating etc.

## Sources
[Aiogram 3 Docs](https://docs.aiogram.dev/)
[About Jira authentification](https://developer.atlassian.com/server/jira/platform/cookie-based-authentication/)
[Jira REST API Docs 9.12.9](https://docs.atlassian.com/software/jira/docs/api/REST/9.12.9/)
