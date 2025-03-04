import sqlite3
from aiohttp import web
from settings import bot


async def jira_issue_update(request: web.Request):
    issue_key = request.match_info["issue_key"]
    data = await request.json()
    status = next(
        (item["toString"] for item in data.get("changelog", {}).get("items", []) if item["field"] == "status"),
        None
    )

    if status:
    
        DB_FILE = "db.sqlite3"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT user_id FROM issues WHERE issue_key = ?", (issue_key,))
        result = cursor.fetchone()
        conn.close()

        if result:

            await bot.send_message(
            chat_id=result[0],
            text=f"Status changed to {status}"
            )

    return web.json_response({"status": "ok"})
