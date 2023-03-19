import builtins
from termcolor import colored
import textwrap


def print(content: str, color: str = 'cyan', indent: int = 0):
    wrapper = textwrap.TextWrapper(
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
        width=150
    )
    parts = content.split("```")
    for i, part in enumerate(parts):
        if i % 2 == 0: builtins.print(colored(wrapper.fill(part), color))
        else: builtins.print(part)
