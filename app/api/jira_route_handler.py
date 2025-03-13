import logging
import sqlite3
from settings import bot, JiraStatuses, i18n
from aiohttp import web
from app.api.jira_rest_api import get_jira_issue_last_comment


# TODO: Needs refactoring, i18n implementation is a joke here
async def jira_issue_update(request: web.Request):
    """Handles webhook post on selected path, notifies user about updates"""

    issue_key = request.match_info["issue_key"]

    DB_FILE = "helpdeskgram.db"
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    cursor = conn.cursor()
    cursor.execute("SELECT user_id, status, locale FROM issues WHERE issue_key = ?", (issue_key,))
    result = cursor.fetchone()

    # No issue with provided issue_key found handling
    if result is None:
        conn.close()
        logging.info(f"No issue with {issue_key} was found.")
        return web.json_response({"status": "ok"})
    else:
        user_id, status, locale = cursor.fetchone()

    if user_id and status != "done":
        data = await request.json()
        status = next(
            (item["toString"] for item in data.get("changelog", {}).get("items", []) if item["field"] == "status"),
            None
        )

        match status:
            case JiraStatuses.APPOINTED:
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext("Your issue <code>{issue_key}</code> appointed to work.", locale=locale).format(issue_key=issue_key)
                )
                cursor.execute("UPDATE issues SET status = ? WHERE issue_key = ?", ("appointed", issue_key))
                conn.commit()
                conn.close()
                logging.info("Issue status changed.")
                return web.json_response({"status": "ok"})
            case JiraStatuses.IN_PROGRESS:
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext("Your issue <code>{issue_key}</code> is currently in progress.", locale=locale).format(issue_key=issue_key)
                )
                cursor.execute("UPDATE issues SET status = ? WHERE issue_key = ?", ("in_progress", issue_key))
                conn.commit()
                conn.close()
                logging.info("Issue status changed.")
                return web.json_response({"status": "ok"})
            case JiraStatuses.DONE:
                last_comment = await get_jira_issue_last_comment(issue_key)
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext("Your issue <code>{issue_key}</code> is done!", locale=locale).format(issue_key=issue_key)
                )
                if last_comment:
                    await bot.send_message(
                        chat_id=user_id,
                        text=last_comment
                    )
                cursor.execute("UPDATE issues SET status = ? WHERE issue_key = ?", ("done", issue_key))
                conn.commit()
                conn.close()
                logging.info("Issue status changed.")
                return web.json_response({"status": "ok"})
            case _:
                logging.info("Status is not in JiraStatuses. Passed.")
                return web.json_response({"status": "ok"})

    else:
        conn.close()
        logging.info("Issue is already done!")
        return web.json_response({"status": "ok"})
