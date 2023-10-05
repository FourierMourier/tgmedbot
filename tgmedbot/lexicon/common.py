from pathlib import Path

from ..constants.common import LEXICON_FILEPATH
from ..constants.bot_const import Commands
from ..utils.common import load_yaml, attributes

from typing import Set, List, Dict, Union, Optional, Any


__all__ = ['Lexicon', 'MissedCommandsException']


class MissedCommandsException(Exception):
    pass


class LexiconModel:
    # en_lang: str = 'en'
    # _supported_languages: Set[str] = {en_lang, 'ru', 'es'}
    NO_COMMAND_FOUND_RESPONSE: str = "Command not found."

    __slots__ = ('_lexicon', )

    def __init__(self, lexicon_filepath: Optional[Union[str, Path]] = None):
        lexicon_filepath = lexicon_filepath or LEXICON_FILEPATH

        self.lexicon: Dict[str, Dict[str, str]] = load_yaml(lexicon_filepath, encoding='utf-8')

    @property
    def lexicon(self) -> Dict[str, Any]:
        return self._lexicon

    @lexicon.setter
    def lexicon(self, value: Dict[str, Dict[str, str]]):
        assert isinstance(value, dict), f"lexicon must be of type dict, got {type(value)}"
        # 1. check if you have all required commands:
        commands_set: Set[str] = set(value.keys())
        attribute_names: List[str] = attributes(Commands)
        attribute_values: Set[str] = set([getattr(Commands, an) for an in attribute_names])
        missed_commands = attribute_values - commands_set
        if missed_commands:
            raise MissedCommandsException(f"Not enough commands: {missed_commands}")
        # 2. check languages
        # for command, lang_to_answer in value.items():
        #     langs_set: Set[str] = set(lang_to_answer.keys())
        #     missing_languages = self._supported_languages - langs_set
        #     if missing_languages:
        #         raise MissedLexiconLanguages(
        #             f"Not enough languages: for command {command}, missing {', '.join(missing_languages)}")

        self._lexicon = value

    def get_response(self, command: str, language: Optional[str] = None):
        # language = language or self.en_lang  # 'en'
        command = command.lstrip('/')
        # command_responses: Union[str, Dict[str, str]] = self.lexicon.get(command, self.no_command_found_response)
        command_response: Union[str, str] = self.lexicon.get(command, self.NO_COMMAND_FOUND_RESPONSE)
        if command_response == self.NO_COMMAND_FOUND_RESPONSE:
            return command_response
        # if language not in command_responses:
        #     raise ValueError(f"Invalid language: {language}")
        # return command_responses.get(language, "Language not found.")
        return command_response


Lexicon = LexiconModel()
