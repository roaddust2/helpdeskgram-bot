from aiogram import Router
from aiogram.filters import Command, CommandStart, StateFilter
from app.keyboards.default import create_issue_ikb, choose_category_ikb
from aiogram import types, html, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from app.handlers.create_issue import CATEGORIES, CreateIssue
from app.db import get_issues
from settings import TIMEZONE

router = Router()


@router.message(CommandStart())
async def cmd_start(message: types.Message) -> None:
    """Main start function"""

    await message.answer(
        _("Greetings, {name}! And welcome to the helpdesk bot").format(
            name=html.quote(message.from_user.full_name)
        ),
        reply_markup=create_issue_ikb()
    )


@router.message(Command("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Anytime cancel and clear state function"""

    await state.clear()
    await message.answer(
        _("Process has been canceled."),
        reply_markup=create_issue_ikb()
    )


@router.callback_query(F.data == "cancel")
async def data_cancel(callback: types.CallbackQuery, state: FSMContext):
    """Cancel and clear state function from inline kb"""

    await callback.message.edit_text(
        text=_("Process has been canceled."),
        reply_markup=create_issue_ikb())
    await state.clear()
    callback.answer()


@router.message(StateFilter(None), Command("create"))
async def choose_category(message: types.CallbackQuery, state: FSMContext):

    message = await message.answer(
        text=_("Choose category:"),
        reply_markup=choose_category_ikb(CATEGORIES)
    )
    await state.update_data(category_message_id=message.message_id)
    await state.set_state(CreateIssue.category)


@router.message(Command("list"))
async def cmd_list(message: types.Message):
    """Function to list all user issues from a command"""

    mapping = {
        "new": _("<code>{issue_key}</code>\n\nNew issue, we will take it to work soon.\nCreated at {created_at} {tz}"),
        "appointed": _("<code>{issue_key}</code>\n\nIssue is already appointed to work!\nCreated at {created_at} {tz}"),
        "in_progress": _("<code>{issue_key}</code>\n\nIssue is currently in progress!\nCreated at {created_at} {tz}"),
    }

    issues = get_issues(message.chat.id)

    if issues:
        for issue in issues:
            issue_key, status, created_at = issue
            await message.answer(
                text=mapping.get(status).format(issue_key=issue_key, created_at=created_at, tz=TIMEZONE)
            )
        await message.answer(
            _("When issue is complete, you will be notified. Do you want to create a new one?"),
            reply_markup=create_issue_ikb()
        )
    else:
        await message.answer(
            text=_("No issues were found, want to create one?"),
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

    issues = get_issues(callback.message.chat.id)

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


@router.message(StateFilter(None))
async def exception_handler(message: types.Message):
    """Catch any unhandled user messages"""

    await message.answer(
        _("Yokozuna Support bot will help you create a support ticket, send it to our team and receive feedback"),
        reply_markup=create_issue_ikb()
    )
