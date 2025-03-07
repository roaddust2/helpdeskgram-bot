import sqlite3
from aiogram import Router, F
from aiogram.filters import Command
from aiogram import types
from aiogram.utils.i18n import gettext as _
from app.keyboards.default import create_issue_ikb
from settings import TIMEZONE


router = Router()


@router.message(Command("list"))
async def cmd_list(message: types.Message):
    """Function to list all user issues from a command"""

    mapping = {
        "new": _("<code>{issue_key}</code>\n\nNew issue, we will take it to work soon.\nCreated at {created_at} {tz}"),
        "appointed": _("<code>{issue_key}</code>\n\nIssue is already appointed to work!\nCreated at {created_at} {tz}"),
        "in_progress": _("<code>{issue_key}</code>\n\nIssue is currently in progress!\nCreated at {created_at} {tz}"),
    }

    DB_FILE = "helpdeskgram.db"
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    cursor = conn.cursor()
    cursor.execute("SELECT issue_key, status, created_at FROM issues WHERE user_id = ?", (message.chat.id,))
    issues = cursor.fetchall()

    for issue in issues:
        issue_key, status, created_at = issue
        await message.answer(
            text=mapping.get(status).format(issue_key=issue_key, created_at=created_at, tz=TIMEZONE)
        )
    await message.answer(
        _("When issue is complete, you will be notified. Do you want to create a new one?"),
        reply_markup=create_issue_ikb()
    )


@router.callback_query(F.data == "list")
async def data_list(callback: types.CallbackQuery):
    """Function to list all user issues from a callback data"""

    await callback.message.delete()
    mapping = {
        "new": _("<code>{issue_key}</code>\n\nNew issue, we will take it to work soon.\nCreated at {created_at} {tz}"),
        "appointed": _("<code>{issue_key}</code>\n\nIssue is already appointed to work!\nCreated at {created_at} {tz}"),
        "in_progress": _("<code>{issue_key}</code>\n\nIssue is currently in progress!\nCreated at {created_at} {tz}"),
    }

    DB_FILE = "helpdeskgram.db"
    conn = sqlite3.connect(DB_FILE, isolation_level=None)
    conn.execute('pragma journal_mode=wal')
    cursor = conn.cursor()
    cursor.execute("SELECT issue_key, status, created_at FROM issues WHERE user_id = ?", (callback.message.chat.id,))
    issues = cursor.fetchall()

    if issues:
        for issue in issues:
            issue_key, status, created_at = issue
            await callback.message.answer(
                text=mapping.get(status).format(issue_key=issue_key, created_at=created_at, tz=TIMEZONE)
            )
        await callback.message.answer(
            text=_("When issue is complete, you will be notified. Do you want to create a new one?"),
            reply_markup=create_issue_ikb()
        )
        callback.answer()
    else:
        await callback.message.answer(
            text=_("No issues were found, want to create one?"),
            reply_markup=create_issue_ikb()
        )
        callback.answer()
