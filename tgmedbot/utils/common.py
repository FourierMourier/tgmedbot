import os
from pathlib import Path
import functools

import yaml

from typing import Union, Dict, Any


__all__ = ['load_yaml', 'methods', 'attributes', 'load_config', 'colorstr', 'infoColorstr', 'warningColorstr',
           'exceptionColorstr']


def load_yaml(filepath: Union[str, Path], **kwargs) -> Dict[str, Any]:
    with open(filepath, 'r', **kwargs) as file:
        config = yaml.safe_load(file)
    return config


def methods(instance):
    # Get class/instance methods
    return [f for f in dir(instance) if callable(getattr(instance, f)) and not f.startswith("__")]


def attributes(instance):
    # Get class/instance attributes
    return [a for a in dir(instance) if not callable(getattr(instance, a)) and not a.startswith("__")]


load_config = load_yaml


def colorstr(*input):
    # Colors a string https://en.wikipedia.org/wiki/ANSI_escape_code, i.e.  colorstr('blue', 'hello world')
    *args, string = input if len(input) > 1 else ('blue', 'bold', input[0])  # color arguments, string
    colors = {'black': '\033[30m',  # basic colors
              'red': '\033[31m',
              'green': '\033[32m',
              'yellow': '\033[33m',
              'blue': '\033[34m',
              'magenta': '\033[35m',
              'cyan': '\033[36m',
              'white': '\033[37m',
              'bright_black': '\033[90m',  # bright colors
              'bright_red': '\033[91m',
              'bright_green': '\033[92m',
              'bright_yellow': '\033[93m',
              'bright_blue': '\033[94m',
              'bright_magenta': '\033[95m',
              'bright_cyan': '\033[96m',
              'bright_white': '\033[97m',
              'end': '\033[0m',  # misc
              'bold': '\033[1m',
              'underline': '\033[4m'}
    return ''.join(colors[x] for x in args) + f'{string}' + colors['end']


# declare partial functions from colorstr:
exceptionColorstr = functools.partial(colorstr, 'bold', 'bright_red')
infoColorstr = functools.partial(colorstr, 'blue', 'bold')
warningColorstr = functools.partial(colorstr, 'bright_yellow', 'bold')
