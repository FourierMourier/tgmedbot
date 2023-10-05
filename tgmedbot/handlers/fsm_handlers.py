import time
import datetime

import aiogram
from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.types import Message, CallbackQuery  # , CallbackGame
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import default_state

from ..fsm import *
from ..keyboards import *
from ..utils.vector_db import *
from ..utils.llm import *
from ..filters import *

import warnings
from typing import Optional


router = Router()


DUMMY_LLM_SPECIAL_TOKEN: str = "__DUMMY_LLM__"


async def _set_state(message: Message, context: FSMContext, next_state: aiogram.fsm.state.State,
                     msg: Optional[str]) -> None:
    print(f"setting state for {message.from_user.id} to {next_state}")
    if msg is not None:
        await message.answer(msg)
    await context.set_state(next_state)


async def _set_state_with_inline_kb(message: Message, context: FSMContext, next_state: aiogram.fsm.state.State,
                                    msg: str, reply_markup) -> None:
    print(f"setting state for {message.from_user.id} to {next_state}")
    await message.answer(msg, reply_markup=reply_markup)
    await context.set_state(next_state)


@router.message(Command(commands=['lm']), StateFilter(default_state))
async def process_get_answer_command(message: Message, state: FSMContext):
    await _set_state(message, state, FSMQueryForm.question_state, "type your query:")


@router.message(StateFilter(FSMQueryForm.question_state), F.text)  # lambda m: m.text
async def process_user_question_message(message: Message, state: FSMContext) -> None:
    user_query = message.text
    # put data into the state
    if DUMMY_LLM_SPECIAL_TOKEN in user_query:
        # check to change the final url to the dummy llm url
        # btw replace special token with ""
        await state.update_data(**{'user_query': user_query.replace(DUMMY_LLM_SPECIAL_TOKEN, "")})
        next_state = FSMQueryForm.dummy_check_state
        await _set_state_with_inline_kb(
            message, state, next_state, f"special token={DUMMY_LLM_SPECIAL_TOKEN} was detected; use llm imitation? :",
            get_bool_selection_inline_keyboard(),
        )
    else:
        next_state = FSMQueryForm.tokens_num_state
        await state.update_data(**{'user_query': user_query})
        await _set_state(message, state, next_state, "type max number of tokens")

    return


# @router.callback_query(StateFilter(FSMQueryForm.dummy_check_state), F.text.startswith(BOOL_SELECTION_MSG_START))
@router.callback_query(StateFilter(FSMQueryForm.dummy_check_state), IsBooleanFilter)
async def process_if_llm_as_dummy(callback: CallbackQuery, state: FSMContext) -> None:
    # boolean_str = callback.data.split(BOOL_SELECTION_MSG_START)[-1]
    bool_answer = get_string_as_bool(callback.data)
    if bool_answer:
        llm_url = DUMMY_PROCESS_QUERY_STREAM_URL
    else:
        llm_url = LLM_PROCESS_QUERY_STREAM_URL
    prev_text: str = callback.message.text or ""
    # remove inline keyboard
    await callback.message.delete_reply_markup()
    # proceed
    await state.update_data(**{'llm_url': llm_url})
    await callback.message.edit_text(f"{prev_text} {bool_answer}")
    await _set_state(callback.message, state, FSMQueryForm.tokens_num_state, "type max number of tokens")


@router.message(StateFilter(FSMQueryForm.tokens_num_state), F.text, F.text.isdigit)
async def process_user_tokens_num_message(message: Message, state: FSMContext) -> None:
    _default_max_tokens_num: int = 256

    user_output = message.text
    try:
        user_max_tokens_num = int(user_output)
    except Exception as E:
        print(f"{E} on casting max tokens")
        await _set_state(message, state, FSMQueryForm.tokens_num_state,
                         f"bad value: {user_output}; try again to set max number of tokens")
        return

    if user_max_tokens_num > _default_max_tokens_num:
        await message.reply(f"your number of max tokens exceeds available and will be set to {_default_max_tokens_num}")

    await _set_state(message, state, FSMQueryForm.response_state, None)
    await state.update_data(**{'max_tokeks_num': user_max_tokens_num})
    await _response_to_user_with_llm(message, state)


async def _response_to_user_with_llm(message: Message, state: FSMContext) -> None:
    # get user data:
    user_data = await state.get_data()
    # clear the state
    await state.clear()
    user_query = user_data.get('user_query', "")
    if user_query == "":
        await message.reply(f"nothing to process for query=\"{user_query}\"")
        return
    max_tokeks_num = user_data.get('max_tokeks_num', 64)
    max_tokeks_num = int(max_tokeks_num)

    # process it using vector db
    # TODO: move it to fsm context as well as add collection name user can work with (must be kinda pagination)
    n_results: int = 2
    collection_name: Optional[str] = None
    # -----------------------------------
    s0 = time.time()
    vector_db_response = await async_process_query(user_query, collection_name, n_results)
    vector_db_response_time = time.time() - s0

    vector_db_documents = vector_db_response.get('documents', None)
    if vector_db_documents is None:
        warnings.warn(f"failed to fetch data from vector db; smth wrong with either backend or database itself")
        vector_db_documents = []
    else:
        vector_db_documents = vector_db_documents[0]
    extended_context = "\n".join(vector_db_documents)

    every_sec = 3
    message_container = []

    s0 = time.time()

    output = ""
    time_delta = datetime.timedelta(seconds=every_sec)
    last_joining_time = datetime.datetime.now()
    llm_response_format = "Response:\n{llm_output}"

    prev_llm_response = llm_response_format.format(llm_output=output)
    reply_message: Optional[Message] = await message.answer(prev_llm_response)
    # retrieve llm_url:
    llm_url = user_data.get('llm_url', LLM_PROCESS_QUERY_STREAM_URL)
    async for chunk in async_process_query_stream(llm_url, user_query, extended_context, max_tokeks_num):
        now = datetime.datetime.now()
        diff = now - last_joining_time
        # print(f"got chunk={chunk} at {diff}")
        if diff >= time_delta:
            # concatenate:
            output += "".join(message_container)
            # print(f"updated with {message_container}")
            llm_response = llm_response_format.format(llm_output=output)
            if llm_response != prev_llm_response:
                try:
                    await reply_message.edit_text(llm_response)
                except Exception as E:
                    print(f"failed on editing text={llm_response}: {E}")
                prev_llm_response = llm_response
            # else:
            # reassign time:
            last_joining_time = now
            # release:
            message_container.clear()

        message_container.append(chunk)

        # check if container is not empty:
    if len(message_container):
        output += "".join(message_container)
        message_container.clear()

    s1 = time.time()

    llm_response_time: float = s1 - s0

    llm_response = llm_response_format.format(llm_output=output)
    await reply_message.edit_text((f"{llm_response}\n\n"
                                   f"llm response time={llm_response_time:.3f} sec\n"
                                   f"vector db response time={vector_db_response_time:.3f} sec"))


