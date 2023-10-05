import datetime

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message, ContentType, CallbackQuery, InlineQuery

from ..constants.bot_const import Commands
from ..lexicon import Lexicon

from sqlalchemy.ext.asyncio import AsyncSession
from ..db.connection import SqliteConnection
from ..db.actions.common import get_user_by_id, add_new_user
from ..schemas.common import UserModel

from aiogram.fsm.context import FSMContext
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import default_state

from typing import Optional


router: Router = Router()


@router.message(Command(commands=Commands.CANCEL), ~StateFilter(default_state))
async def process_cancel_command_state(message: Message, state: FSMContext):
    await state.clear()
    await message.answer(text='✅ has cleared state')


@router.message(Command(commands=Commands.CANCEL), StateFilter(default_state))
async def process_cancel_command_out_state(message: Message):
    await message.answer(text="♻️ nothing to cancel: no state has been entered")


@router.message(Command(commands=[Commands.START]))
async def process_start_command(message: Message) -> None:
    user_id: int = message.from_user.id

    async with SqliteConnection.get_session() as session:
        user: Optional[UserModel] = await get_user_by_id(session, user_id)

        lang: Optional[str] = None
        curr_dt = datetime.datetime.now()
        if user is None:
            await add_new_user(session, user_id, curr_dt)
            print(f"user with id = {user_id} was inserted: {user}")

        else:
            lang = user.lang

        await message.answer(Lexicon.get_response(Commands.START, lang))


@router.message(Command(commands=[Commands.HELP]))
async def process_help_command(message: Message) -> None:

    lang: Optional[str] = None
    user_id: int = message.from_user.id
    async with SqliteConnection.get_session() as session:
        user: Optional[UserModel] = await get_user_by_id(session, user_id)
        if user is not None:
            lang = user.lang

    await message.answer(Lexicon.get_response(Commands.HELP, lang))


@router.message(Command(commands=[Commands.ABOUT]))
async def process_about_command(message: Message) -> None:
    lang: Optional[str] = None
    user_id: int = message.from_user.id
    async with SqliteConnection.get_session() as session:
        user: Optional[UserModel] = await get_user_by_id(session, user_id)
        if user is not None:
            lang = user.lang

    await message.answer(Lexicon.get_response(Commands.ABOUT, lang))


@router.message()
async def process_other_text_answers(message: Message):
    user_id: int = message.from_user.id

    async with SqliteConnection.get_session() as session:
        user: Optional[UserModel] = await get_user_by_id(session, user_id)
        lang: Optional[str] = None
        if user is not None:
            lang = user.lang

        await message.answer(Lexicon.get_response(Commands.OTHER_MESSAGES, lang))
