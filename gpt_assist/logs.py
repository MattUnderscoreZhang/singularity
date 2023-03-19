import builtins
from dataclasses import dataclass, field
import os
from pathlib import Path
import pickle as pk
from termcolor import colored
import textwrap
import tiktoken
from typing import Any, Dict, List

from gpt_assist.color_scheme import Colors
from gpt_assist.gpt import gpt_api


@dataclass
class Message:
    role: str
    content: str
    persist: bool = False

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


@dataclass
class Log:
    model: str
    log: List[Message] = field(default_factory=list)
    prune_trigger: int = 3500

    def append(self, message: Message):
        self.log.append(message)
        if self.length > self.prune_trigger:
            self.prune()
        # TODO: autosave

    def __str__(self) -> str:
        return "\n".join([str(message) for message in self.log])

    def __add__(self, other: "Log") -> "Log":
        new_log = Log(self.model, self.log + other.log)
        if new_log.length > self.prune_trigger:
            new_log.prune()
        return new_log
        # TODO: autosave

    def __save__(self):
        save_dir = Path(os.getcwd()) / "saved_logs"
        n_saved_logs = len([f for f in os.listdir(save_dir) if os.path.isfile(f)])
        save_path = save_dir / f"log_{n_saved_logs}.txt"
        pk.dump(self, open(save_path, "wb"))

    @property
    def length(self) -> int:
        enc = tiktoken.encoding_for_model(self.model)
        return sum([
            len(enc.encode(message.content))
            for message in self.log
        ])

    def __iter__(self):
        return iter(self.log)

    def pop(self) -> Message:
        return self.log.pop()

    def prune(self):
        """Prune the log to a reasonable number of tokens."""
        messages = [
            message
            for message in self.log
            if not message.persist
        ]
        messages.append(
            Message(
                role="user",
                content=(
                    "Write a short summary of what we've said so far that I can give you "
                    "later if we were to continue this conversation. Do not add a preamble "
                    "or postamble to this summary."
                ),
            )
        )
        summary = gpt_api(Log(self.model, messages).to_messages(), self.model, 1)
        new_log = [
            message
            for message in self.log
            if message.persist
        ] + [Message(role="user", content=summary)] + self.log[-5:]
        self.log = new_log

    def to_messages(self) -> List[Dict]:
        messages = [
            {
                "role": m.role,
                "content": m.content
            }
            for m in self.log
        ]
        return messages


def load_log(file_path: Path) -> Log:
    with open(file_path, "rb") as f:
        return pk.load(f)


def print(content: Any = "", color: str = Colors.info, indent: int = 0, end: str = '\n'):
    content = str(content)
    wrapper = textwrap.TextWrapper(
        initial_indent=" " * indent,
        subsequent_indent=" " * indent,
        width=150
    )
    parts = content.split("```")
    for i, part in enumerate(parts):
        # if i % 2 == 0: builtins.print(colored(wrapper.fill(part), color))
        if i % 2 == 0: builtins.print(colored(part, color), end=end)
        else: builtins.print(colored(part, Colors.code), end=end)
