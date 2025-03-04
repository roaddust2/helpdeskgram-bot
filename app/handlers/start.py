from aiogram import Router
from aiogram.filters import Command, CommandStart
from app.keyboards.default import create_issue_ikb
from aiogram import types, html, F
from aiogram.fsm.context import FSMContext
from aiogram.utils.i18n import gettext as _
from aiogram.utils.i18n import lazy_gettext as __


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
@router.message(F.text.lower() == __("cancel"))
async def cmd_cancel(message: types.Message, state: FSMContext):
    """Anytime cancel and clear state function"""

    await state.clear()
    await message.answer(
        _("Process has been canceled."),
        reply_markup=create_issue_ikb()
    )
