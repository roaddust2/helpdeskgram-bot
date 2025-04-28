from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _
from settings import i18n


def create_issue_ikb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=_("Create new issue"), callback_data="create_new_issue"))
    builder.row(InlineKeyboardButton(text=_("My issues"), callback_data="list"))
    return builder.as_markup()


def create_issue_manual_locale_ikb(locale) -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text=i18n.gettext(
        "Create new issue",
        locale=locale), callback_data="create_new_issue"))
    builder.row(InlineKeyboardButton(text=i18n.gettext("My issues", locale=locale), callback_data="list"))
    return builder.as_markup()


def confirm_issue_ikb() -> InlineKeyboardBuilder:
    buttons = [
        [
            types.InlineKeyboardButton(text=_("Cancel"), callback_data="cancel"),
            types.InlineKeyboardButton(text=_("Submit"), callback_data="submit")
        ]
    ]
    keyboard = types.InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def choose_category_ikb(buttons: list[tuple[str, str]]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()

    for button in buttons:
        builder.row(
            InlineKeyboardButton(text=_(button[0]), callback_data=button[1])
        )
    builder.row(
        InlineKeyboardButton(text=_("Cancel"), callback_data="cancel")
    )
    return builder.as_markup()


def share_contact_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=_("Share your contact"), request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def skip_ikb() -> InlineKeyboardBuilder:
    keyboard = types.InlineKeyboardMarkup(
        inline_keyboard=[[types.InlineKeyboardButton(text=_("Skip"), callback_data="skip"),]]
    )
    return keyboard
