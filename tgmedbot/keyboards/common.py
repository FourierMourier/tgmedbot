from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Optional, Dict, Any, Iterable


__all__ = ['get_bool_selection_inline_keyboard', 'BOOL_SELECTION_MSG_START']

BOOL_SELECTION_MSG_START: str = '_boolean_selection_'


def create_inline_keyboard(width: int, *args, **kwargs) -> InlineKeyboardBuilder:

    kb_builder = InlineKeyboardBuilder()
    buttons: List[InlineKeyboardButton] = []
    if args:
        for button_str in args:
            buttons.append(
                # TODO: change text being SomeClassOrDict[button]
                InlineKeyboardButton(text=button_str, callback_data=button_str)
            )

    if kwargs:
        for button, text in kwargs.items():
            buttons.append(InlineKeyboardButton(
                text=text,
                callback_data=button))

    kb_builder.row(*buttons, width=width)
    return kb_builder


def create_inline_keyboard_markup(width: int, *args, **kwargs) -> InlineKeyboardMarkup:

    kb_builder = create_inline_keyboard(width, *args, **kwargs)
    return kb_builder.as_markup()


def get_bool_selection_inline_keyboard() -> InlineKeyboardMarkup:
    button_texts: dict = dict()
    width: int = 2
    for s in ('True', 'False'):
        # button_texts[f"{BOOL_SELECTION_MSG_START}{s}"] = s
        button_texts[f"{s}"] = s

    return create_inline_keyboard_markup(width, **button_texts)

