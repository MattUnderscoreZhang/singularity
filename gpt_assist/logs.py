import builtins
from dataclasses import dataclass, field
from termcolor import colored
import textwrap
from typing import Any, List


@dataclass
class Message:
    role: str
    content: str
    preamble: bool = False

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"

    @property
    def length(self) -> int:
        return len(self.content)


@dataclass
class Log:
    log: List[Message] = field(default_factory=list)

    def append(self, message: Message):
        self.log.append(message)

    def __str__(self) -> str:
        return "\n".join([str(message) for message in self.log])

    @property
    def length(self) -> int:
        return sum([message.length for message in self.log])

    def __iter__(self):
        return iter(self.log)


def print(content: Any = "", color: str = 'cyan', indent: int = 0):
    content = str(content)
    wrapper = textwrap.TextWrapper(
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
        width=150
    )
    parts = content.split("```")
    for i, part in enumerate(parts):
        # if i % 2 == 0: builtins.print(colored(wrapper.fill(part), color))
        if i % 2 == 0: builtins.print(colored(part, color))
        else: builtins.print(part)
