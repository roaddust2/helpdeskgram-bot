from aiogram import Router
from aiogram.filters import Command, CommandStart
from app.keyboards.default import create_issue_ikb
from aiogram import types, html, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.filters import StateFilter


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

    await callback.message.delete()
    await state.clear()
    await callback.message.answer(
        _("Process has been canceled."),
        reply_markup=create_issue_ikb()
    )
    callback.answer()


@router.message(StateFilter(None))
async def exception_handler(message: types.Message):
    """Cancel and clear state function from inline kb"""

    await message.answer(
        _("Yokozuna Support bot will help you create a support ticket, send it to our team and receive feedback"),
        reply_markup=create_issue_ikb()
    )
