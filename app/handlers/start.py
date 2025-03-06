from aiogram import Router
from aiogram.filters import Command, CommandStart
from app.keyboards.default import create_issue_ikb
from aiogram import types, html, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _


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
