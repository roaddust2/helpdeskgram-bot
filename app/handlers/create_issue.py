import sqlite3
from datetime import datetime
from app.api.jira_rest_api import create_jira_issue, upload_jira_issue_attachments
from app.keyboards.default import (
    choose_category_kb,
    create_issue_ikb,
    share_contact_kb,
    confirm_issue_ikb,
    skip_kb
)
from aiogram import Bot, Router, F
from aiogram import types
from aiogram.filters import StateFilter
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from settings import JIRA_PROJECT, JIRA_ISSUE_TYPE


router = Router()


class CreateIssue(StatesGroup):
    category = State()
    description = State()
    screenshots = State()
    contact = State()
    confirmation = State()


available_categories = [
    __("dealer's calculator"),
    __("client's calculator"),
    __("tracking"),
    __("translations"),
    __("mobile"),
    __("other")
]


# Choose category

@router.callback_query(StateFilter(None), F.data == "create_new_issue")
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.answer(
        text=_("Choose category:"),
        reply_markup=choose_category_kb()
    )
    await state.set_state(CreateIssue.category)
    await callback.answer()


@router.message(
    CreateIssue.category,
    F.text.lower().in_(available_categories)
)
async def category_chosen(message: types.Message, state: FSMContext):
    await state.update_data(category=message.text)
    await message.answer(
        text=_("Thank you! Now describe your problem in details:")
    )
    await state.set_state(CreateIssue.description)


@router.message(CreateIssue.category)
async def category_chosen_incorrectly(message: types.Message):
    await message.answer(
        text=_("The category you entered is incorrect, please choose from the above:"),
        reply_markup=choose_category_kb()
    )


# Input description

@router.message(CreateIssue.description, F.text)
async def input_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await message.answer(
        text=_("Add up to 3 screenshots (optional):"),
        reply_markup=skip_kb()
    )
    await state.update_data(screenshots=[])
    await state.set_state(CreateIssue.screenshots)


@router.message(CreateIssue.description)
async def description_inputed_incorrectly(message: types.Message):
    await message.answer(
        text=_("You must provide a description:"),
        reply_markup=choose_category_kb()
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
                reply_markup=skip_kb()
            )
        else:
            await message.answer(
                text=_("You uploaded maximum amount of screenshots. Please, share your contact."),
                reply_markup=share_contact_kb()
            )
            await state.set_state(CreateIssue.contact)


@router.message(CreateIssue.screenshots, F.text.lower() == __("skip"))
async def skip_screenshots(message: types.Message, state: FSMContext):
    await message.answer(
        text=_("Please, share your contact"),
        reply_markup=share_contact_kb()
    )
    await state.set_state(CreateIssue.contact)


# Share contact

@router.message(CreateIssue.contact, F.contact)
async def confirm_request(message: types.Message, state: FSMContext):
    await state.update_data(contact=message.contact)
    issue = await state.get_data()
    screenshots = issue.get('screenshots')
    await message.answer(
        text=_(
            "Submit your request\n\n"
            "Category: {category}\n"
            "Description: {description}\n"
            "Screenshots: {number} added\n"
            "Contact: {first_name} {phone_number}").format(
                category=issue.get('category'),
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
                "labels": [issue.get('category').replace(" ", "_"), issue.get('contact').first_name, issue.get('contact').phone_number],
            }
        )

        await upload_jira_issue_attachments(issue_key, screenshots)

        DB_FILE = "db.sqlite3"
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO issues (user_id, issue_key, created_at) VALUES (?, ?, ?)",
            (callback.message.from_user.id, issue_key, datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
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
