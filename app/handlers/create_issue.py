# TODO: NEED REFACTORING
import logging
import re
from aiogram import Bot, Router, F, types
from aiogram.filters import StateFilter
from aiogram.utils.chat_action import ChatActionSender
from aiogram.utils.i18n import I18n
from aiogram.utils.i18n import gettext as _
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from settings import JIRA_PROJECT, JIRA_ISSUE_TYPE, CATEGORIES
from app.api.jira_rest_api import JiraFailure, create_jira_issue, upload_jira_issue_attachments
from app.db import get_user_id, insert_issue, insert_user, get_user_contact
from app.keyboards.default import (
    choose_category_ikb,
    create_issue_ikb,
    share_contact_kb,
    confirm_issue_ikb,
    skip_ikb
)


router = Router()


# Availible FSM states

class CreateIssue(StatesGroup):
    category = State()
    description = State()
    attachments = State()
    contact = State()
    confirmation = State()


# CHOOSE CATEGORY

@router.callback_query(StateFilter(None), F.data == "create_new_issue")
async def choose_category(callback: types.CallbackQuery, state: FSMContext):
    """
    Entrypoint to issue creation FSM
    Asks user to choose category from list
    """

    message = await callback.message.edit_text(
        text=_("Choose category:"),
        reply_markup=choose_category_ikb(CATEGORIES)
    )
    await state.update_data(category_message_id=message.message_id)
    await state.set_state(CreateIssue.category)
    await callback.answer()


@router.callback_query(CreateIssue.category, F.data.in_({callback for _, callback in CATEGORIES}))
async def category_chosen(callback: types.CallbackQuery, state: FSMContext):
    """
    When user have chosen category
    Changes state to description
    """

    await state.update_data(category_message_id=None)
    await state.update_data(category=callback.data)
    await callback.message.edit_text(
        text=_("Thank you! Now describe your problem in details:")
    )
    await state.set_state(CreateIssue.description)
    await callback.answer()


@router.message(CreateIssue.category)
async def category_chosen_incorrectly(message: types.Message, state: FSMContext):
    """FSM Exception, if user input is incorrect"""

    data = await state.get_data()
    message_id = data.get("category_message_id", None)

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


# INPUT DESCRIPTION

@router.message(CreateIssue.description, F.text)
async def input_description(message: types.Message, state: FSMContext):
    """When description entered correctly, switch to next state"""

    await state.update_data(description=message.text)
    await message.answer(
        text=_("Add attachments. You can upload up to 5 attachments (photo or minute video) or press <b>Skip</b>"),
        reply_markup=skip_ikb()
    )
    await state.set_state(CreateIssue.attachments)


@router.message(CreateIssue.description)
async def description_inputed_incorrectly(message: types.Message):
    """FSM Exception, if user input is not a text message"""

    await message.answer(
        text=_("You must provide a description:")
    )


# UPLOAD ATTACHMENTS

@router.message(CreateIssue.attachments, F.photo | F.video)
async def add_attachments(message: types.Message, bot: Bot, state: FSMContext):
    """FSM stage that allows user to upload attachments"""

    issue = await state.get_data()
    attachments = issue.get("attachments", [])
    contact = get_user_contact(message.chat.id)

    if len(attachments) < 5:
        if message.photo:
            photo_file = await bot.download(message.photo[-1].file_id)
            photo_name = f"{message.photo[-1].file_id}.jpg"
            attachments.append((photo_file, photo_name))
            await state.update_data(attachments=attachments)
        
        elif message.video:
            if message.video.duration > 60:
                await message.answer(
                    text=_("The video is too long. Please upload a video that is 60 seconds or shorter.")
                )
            else:
                video_file = await bot.download(message.video.file_id)
                video_name = f"{message.video.file_id}.mp4"
                attachments.append((video_file, video_name))
                await state.update_data(attachments=attachments)
        
        else:
            await message.answer(
                    text=_("Only photo or video attachments are supported!"),
                )
        
        if len(attachments) < 5:
            await message.answer(
                text=_("{} of 5 added! Add more or press <b>Skip</b>").format(len(attachments)),
                reply_markup=skip_ikb()
            )

    issue = await state.get_data()
    if len(issue.get("attachments", [])) == 5:
        if contact:
            category = [category for category, data in CATEGORIES if issue.get('category') == data]
            await message.answer(
                text=_(
                    "Submit your request\n\n"
                    "<b>Category:</b> {category}\n"
                    "<b>Description:</b> {description}\n"
                    "<b>Attachments:</b> {number} added\n"
                    "<b>Contact:</b> {first_name} {phone_number}").format(
                        category=_(category[0]),
                        description=issue.get('description'),
                        number=len(issue.get('attachments', [])),
                        first_name=contact[0],
                        phone_number=contact[1]
                ),
                reply_markup=confirm_issue_ikb()
            )
            await state.set_state(CreateIssue.confirmation)
        else:
            await message.answer(
                text=_("You have uploaded all attachments. Please, share your contact."),
                reply_markup=share_contact_kb()
            )
            await state.set_state(CreateIssue.contact)


# SKIP ATTACHMENTS

@router.callback_query(CreateIssue.attachments, F.data == "skip")
async def skip_attachments(callback: types.CallbackQuery, state: FSMContext):
    """If user pressed 'Skip', swithes to contact share or confirmation"""

    contact = get_user_contact(callback.message.chat.id)
    if contact:
        issue = await state.get_data()
        category = [category for category, data in CATEGORIES if issue.get('category') == data]
        attachments = issue.get('attachments')
        await callback.message.edit_text(
            text=_(
                "Submit your request\n\n"
                "<b>Category:</b> {category}\n"
                "<b>Description:</b> {description}\n"
                "<b>Attachments:</b> {number} added\n"
                "<b>Contact:</b> {first_name} {phone_number}").format(
                    category=_(category[0]),
                    description=issue.get('description'),
                    number=len(attachments) if attachments else 0,
                    first_name=contact[0],
                    phone_number=contact[1]
            ),
            reply_markup=confirm_issue_ikb()
        )
        await state.set_state(CreateIssue.confirmation)
        await callback.answer()
    else:
        await callback.message.answer(
            text=_("Please, share your contact"),
            reply_markup=share_contact_kb()
        )
        await state.set_state(CreateIssue.contact)
        await callback.answer()


# SHARE CONTACT

@router.message(CreateIssue.contact, F.contact)
async def confirm_request(message: types.Message, state: FSMContext):
    """Confirm request state"""

    await state.update_data(contact=message.contact)
    issue = await state.get_data()
    category = [category for category, data in CATEGORIES if issue.get('category') == data]
    attachments = issue.get('attachments')
    await message.answer(
        text=_(
            "Submit your request\n\n"
            "<b>Category:</b> {category}\n"
            "<b>Description:</b> {description}\n"
            "<b>Attachments:</b> {number} added\n"
            "<b>Contact:</b> {first_name} {phone_number}").format(
                category=_(category[0]),
                description=issue.get('description'),
                number=len(attachments) if attachments else 0,
                first_name=issue.get('contact').first_name,
                phone_number=issue.get('contact').phone_number
        ),
        reply_markup=confirm_issue_ikb()
    )
    await state.set_state(CreateIssue.confirmation)


@router.message(CreateIssue.contact, F.photo | F.video | F.text)
async def add_attachments_exceeded(message: types.Message, state: FSMContext):
    await message.answer(
        text=_("You already uploaded attachments. Please, share your contact."),
        reply_markup=share_contact_kb()
    )


@router.message(CreateIssue.contact, F.text)
async def add_attachments_exceeded_text(message: types.Message, state: FSMContext):
    await message.answer(
        text=_("Please, share your contact. Click the button below:"),
        reply_markup=share_contact_kb()
    )


# ISSUE CONFIRMATION

@router.callback_query(CreateIssue.confirmation, F.data == "submit")
async def process_confirm(callback: types.CallbackQuery, state: FSMContext, i18n: I18n):

    issue = await state.get_data()
    description = issue.get('description')
    # Jira don't allow newline characters in summary field
    clean_description = re.sub(r'\s+', ' ', description).strip()
    summary = clean_description[:50] + "..." if len(clean_description) > 50 else clean_description
    attachments = issue.get('attachments')
    locale = i18n.ctx_locale.get()

    if issue.get('contact'):
        first_name = issue.get('contact').first_name
        phone_number = issue.get('contact').phone_number
    else:
        first_name, phone_number = get_user_contact(callback.message.chat.id)

    async with ChatActionSender.typing(bot=callback.bot, chat_id=callback.message.chat.id):
        try:
            await callback.message.edit_reply_markup(reply_markup=None)

            issue_key = issue.get("issue_key")

            if not issue_key:
                issue_key = await create_jira_issue({
                    "project": {"id": JIRA_PROJECT},
                    "issuetype": {"id": JIRA_ISSUE_TYPE},
                    "customfield_10108": "YOK-584",
                    "summary": summary,
                    "description": description,
                    "labels": [issue.get('category'), first_name, phone_number],
                })
                await state.update_data(issue_key=issue_key)

            if attachments:
                await upload_jira_issue_attachments(issue_key, attachments)

            user = get_user_id(callback.from_user.id)
            if user:
                user_id = user[0]
                insert_issue(user_id, issue_key)
            else:
                user_id = insert_user(callback.from_user.id, first_name, phone_number, locale)
                insert_issue(user_id, issue_key)

            await callback.message.edit_text(
                text=_(
                    "Your request <code>{issue_key}</code> has been submitted. "
                    "We will help you as soon as possible!"
                ).format(issue_key=issue_key),
                reply_markup=create_issue_ikb()
            )
            await state.clear()
            await callback.answer()

        except JiraFailure as err:
            logging.error(err)
            await callback.message.edit_text(
                text=_("Something went wrong, try again after few minutes!"),
                reply_markup=create_issue_ikb()
            )
            await callback.answer()


@router.callback_query(CreateIssue.confirmation, F.data == "cancel")
async def process_cancel(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        text=_("Request canceled."),
        reply_markup=create_issue_ikb()
    )
    await state.clear()
    await callback.answer()
