from aiogram import types
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder, InlineKeyboardBuilder
from aiogram.utils.i18n import gettext as _


def create_issue_ikb() -> InlineKeyboardBuilder:
    builder = InlineKeyboardBuilder()
    builder.add(InlineKeyboardButton(
        text=_("Create new issue"),
        callback_data="create_new_issue")
    )
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


def choose_category_kb() -> ReplyKeyboardMarkup:
    """Main keyboard with most usable menu buttons"""
    builder = ReplyKeyboardBuilder()
    builder.row(
        KeyboardButton(text=_("Dealer's calculator")),
        KeyboardButton(text=_("Client's calculator"))
    )
    builder.row(
        KeyboardButton(text=_("Tracking")),
        KeyboardButton(text=_("Translations"))
    )
    builder.row(
        KeyboardButton(text=_("Mobile")),
        KeyboardButton(text=_("Other"))
    )
    builder.row(
        KeyboardButton(text=_("Cancel"))
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def share_contact_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=_("Share your contact"), request_contact=True)
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)


def skip_kb() -> ReplyKeyboardMarkup:
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text=_("Skip"))
    )
    return builder.as_markup(resize_keyboard=True, one_time_keyboard=True)
