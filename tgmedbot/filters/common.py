"""
    This module contains some basic filters for aiogram handlers
"""
import warnings

import aiogram
from aiogram.types import Message, CallbackQuery
from aiogram.filters import BaseFilter, Filter

from ..utils.common import warningColorstr

from typing import Union, Optional


__all__ = ['get_string_as_bool', 'IsBooleanFilter']


def get_string_as_bool(boolean_str) -> bool:
    boolean_str = boolean_str.lower()
    if boolean_str == 'true':
        return True
    elif boolean_str == 'false':
        return False
    else:
        warnings.warn(warningColorstr(f"Invalid boolean string: {boolean_str}"))
        return False


def _check_str_from_update_as_bool(aiogram_type: Union[Message, CallbackQuery], *args, **kwargs) -> bool:
    boolean_str: Optional[str]
    if isinstance(aiogram_type, Message):
        boolean_str = aiogram_type.text
    elif isinstance(aiogram_type, CallbackQuery):
        boolean_str = aiogram_type.message.text
    else:
        warnings.warn(warningColorstr(f"Unknown update type: {type(aiogram_type)}; returning False"))
        return False

    if boolean_str is None:
        return False

    return get_string_as_bool(boolean_str)


class IsBooleanFilter(BaseFilter):
    def __init__(self, *args, **kwargs):  # to prevent errors during init allow to pass any *args, **kwargs
        # print(f"args: {args}\nkwargs: {kwargs}")
        super().__init__()

    async def __call__(self, aiogram_type: Union[Message, CallbackQuery], *args, **kwargs) -> bool:
        # TODO: add the same class but for kinda IsBooleanFilterButAdmin where you can allow this only for admin users
        return _check_str_from_update_as_bool(aiogram_type, *args, **kwargs)
