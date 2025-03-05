import sqlite3
from datetime import datetime
from app.api.jira_rest_api import create_jira_issue, upload_jira_issue_attachments
from app.keyboards.default import (
    choose_category_ikb,
    create_issue_ikb,
    share_contact_kb,
    confirm_issue_ikb,
    skip_ikb
)
from aiogram import Bot, Router, F
from aiogram import types
from aiogram.filters import StateFilter
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from settings import JIRA_PROJECT, JIRA_ISSUE_TYPE, CATEGORIES


router = Router()


class CreateIssue(StatesGroup):
    category = State()
    description = State()
    screenshots = State()
    contact = State()
    confirmation = State()


# Choose category

@router.callback_query(StateFilter(None), F.data == "create_new_issue")
async def choose_category(callback: types.CallbackQuery, state: FSMContext):

    await callback.message.delete()
    message = await callback.message.answer(
        text=_("Choose category:"),
        reply_markup=choose_category_ikb(CATEGORIES)
    )
    await state.update_data(category_message_id=message.message_id)
    await state.set_state(CreateIssue.category)
    await callback.answer()


@router.callback_query(CreateIssue.category, F.data.in_({callback for _, callback in CATEGORIES}))
async def category_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.delete()
    await state.update_data(category_message_id=None)
    await state.update_data(category=callback.data)
    await callback.message.answer(
        text=_("Thank you! Now describe your problem in details:")
    )
    await state.set_state(CreateIssue.description)
    await callback.answer()


@router.message(CreateIssue.category)
async def category_chosen_incorrectly(message: types.Message, state: FSMContext):
    data = await state.get_data()
    message_id = data.get("category_message_id")

    if message_id:
        try:
            await message.bot.delete_message(chat_id=message.chat.id, message_id=message_id)
        except Exception:
            pass

    new_message = await message.answer(
        text=_("The category you entered is incorrect, please press a button below:"),
        reply_markup=choose_category_ikb(CATEGORIES)
    )
    await state.update_data(category_message_id=new_message.message_id)


# Input description

@router.message(CreateIssue.description, F.text)
async def input_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        text=_("Add up to 3 screenshots (optional):"),
        reply_markup=skip_ikb()
    )
    await state.update_data(screenshots=[])
    await state.set_state(CreateIssue.screenshots)


@router.message(CreateIssue.description)
async def description_inputed_incorrectly(message: types.Message):
    await message.answer(
        text=_("You must provide a description:")
    )


# Add screenshots

@router.message(CreateIssue.screenshots, F.photo)
async def add_screenshots(message: types.Message, bot: Bot, state: FSMContext):
    issue = await state.get_data()
    screenshots = issue.get("screenshots", [])

    if len(screenshots) < 3:
        photo_file = await bot.download(message.photo[-1].file_id)
        photo_name = f"{message.photo[-1].file_id}.jpg"
        screenshots.append((photo_file, photo_name))
        await state.update_data(screenshots=screenshots)

        if len(screenshots) < 3:
            await message.answer(
                text=_("Add another screenshot or press Skip"),
                reply_markup=skip_ikb()
            )
        else:
            await message.answer(
                text=_("You uploaded maximum amount of screenshots. Please, share your contact."),
                reply_markup=share_contact_kb()
            )
            await state.set_state(CreateIssue.contact)


@router.callback_query(CreateIssue.screenshots, F.data == "skip")
async def skip_screenshots(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=_("Please, share your contact"),
        reply_markup=share_contact_kb()
    )
    await state.set_state(CreateIssue.contact)
    await callback.answer()


# Share contact

@router.message(CreateIssue.contact, F.contact)
async def confirm_request(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.contact)
    issue = await state.get_data()
    category = {category for category, data in CATEGORIES if issue.get('category') == data}
    screenshots = issue.get('screenshots')
    await message.answer(
        text=_(
            "Submit your request\n\n"
            "Category: {category}\n"
            "Description: {description}\n"
            "Screenshots: {number} added\n"
            "Contact: {first_name} {phone_number}").format(
                category=category[0],
                description=issue.get('description'),
                number=len(screenshots) if screenshots else 0,
                first_name=issue.get('contact').first_name,
                phone_number=issue.get('contact').phone_number
        ),
        reply_markup=confirm_issue_ikb()
    )
    await state.set_state(CreateIssue.confirmation)


@router.message(CreateIssue.contact, F.photo)
async def add_screenshots_exceeded_photo(message: types.Message, state: FSMContext):
    await message.answer(
        text=_("You uploded maximum amount of screenshots. Please, share your contact."),
        reply_markup=share_contact_kb()
    )


@router.message(CreateIssue.contact, F.text)
async def add_screenshots_exceeded_text(message: types.Message, state: FSMContext):
    await message.answer(
        text=_("Please, share your contact. Click the button below:"),
        reply_markup=share_contact_kb()
    )


@router.callback_query(CreateIssue.confirmation, F.data == "submit")
async def process_confirm(callback: types.CallbackQuery, state: FSMContext):

    issue = await state.get_data()
    screenshots = issue.get('screenshots')

    try:
        issue_key = await create_jira_issue(
            {
                "project": {
                    "id": JIRA_PROJECT
                },
                "issuetype": {
                    "id": JIRA_ISSUE_TYPE
                },
                "customfield_10108": "YOK-584",
                "summary": f"{' '.join(issue.get('description').split()[:5])}...",
                "description": issue.get('description'),
                "labels": [issue.get('category'), issue.get('contact').first_name, issue.get('contact').phone_number],
            }
        )

        await upload_jira_issue_attachments(issue_key, screenshots)

        DB_FILE = "db.sqlite3"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issues (user_id, issue_key, created_at) VALUES (?, ?, ?)",
            (callback.from_user.id, issue_key, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
        )
        conn.commit()
        conn.close()

        await callback.message.answer(
            text=_("Your request #{issue_key} has been submited. We will help you as soon as possible!").format(
                issue_key=issue_key
            )
        )
        await state.clear()
        await callback.answer()

    except Exception as err:
        print(f"Something went wrong! {err}")


@router.callback_query(CreateIssue.confirmation, F.data == "cancel")
async def process_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=_("Request canceled."),
        reply_markup=create_issue_ikb()
    )
    await state.clear()
    await callback.answer()
