from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.filters.state import State, StatesGroup


__all__ = ['FSMQueryForm']


class FSMQueryForm(StatesGroup):
    # topic = State()  # TODO: allow user to setup the topic to use an appropriate vector database collection
    question_state = State()
    dummy_check_state = State()  # will be activated if special token for llm imitation will be detected
    tokens_num_state = State()
    response_state = State()  # at this state do not respond
