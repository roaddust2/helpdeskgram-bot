import logging
from settings import bot, JiraStatuses, i18n
from aiohttp import web
from app.api.jira_rest_api import get_jira_issue_last_comment
from app.keyboards.default import create_issue_manual_locale_ikb
from app.db import get_issue, update_issue_status


# TODO: Needs refactoring, i18n implementation is a joke here
async def jira_issue_update(request: web.Request):
    """Handles webhook post on selected path, notifies user about updates"""

    issue_key = request.match_info["issue_key"]

    issue = get_issue(issue_key)

    # No issue with provided issue_key found handling
    if issue is None:
        logging.info(f"No issue with {issue_key} was found.")
        return web.json_response({"status": "ok"})
    else:
        user_id, status, locale = issue

    if user_id and status != "done":
        data = await request.json()
        status = next(
            (item["toString"] for item in data.get("changelog", {}).get("items", []) if item["field"] == "status"),
            None
        )

        match status:
            case JiraStatuses.APPOINTED:
                status = "appointed"
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext(
                        "Your issue <code>{issue_key}</code> appointed to work.",
                        locale=locale).format(issue_key=issue_key),
                    reply_markup=create_issue_manual_locale_ikb(locale=locale)
                )
                update_issue_status(issue_key, status)
                return web.json_response({"status": "ok"})
            case JiraStatuses.IN_PROGRESS:
                status = "in_progress"
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext(
                        "Your issue <code>{issue_key}</code> is currently in progress.",
                        locale=locale).format(issue_key=issue_key),
                    reply_markup=create_issue_manual_locale_ikb(locale=locale)
                )
                update_issue_status(issue_key, status)
                return web.json_response({"status": "ok"})
            case JiraStatuses.DONE:
                status = "done"
                last_comment = await get_jira_issue_last_comment(issue_key)
                await bot.send_message(
                    chat_id=user_id,
                    text=i18n.gettext(
                        "Your issue <code>{issue_key}</code> is done!",
                        locale=locale).format(issue_key=issue_key),
                    reply_markup=create_issue_manual_locale_ikb(locale=locale)
                )
                if last_comment:
                    await bot.send_message(
                        chat_id=user_id,
                        text=last_comment
                    )
                update_issue_status(issue_key, status)
                return web.json_response({"status": "ok"})
            case _:
                logging.info("Status is not in JiraStatuses. Passed.")
                return web.json_response({"status": "ok"})

    else:
        logging.info("Issue is already done!")
        return web.json_response({"status": "ok"})
