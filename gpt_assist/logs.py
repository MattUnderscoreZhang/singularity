import builtins
from dataclasses import dataclass, field
import os
from pathlib import Path
import pickle as pk
from termcolor import colored
import textwrap
import tiktoken
from typing import Any, Dict, List, Optional

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
    save_name: Optional[str] = None

    def append(self, message: Message) -> None:
        self.log.append(message)
        if self.length > self.prune_trigger:
            self.prune()
        self.__save__()

    def __str__(self) -> str:
        return "\n".join([str(message) for message in self.log])

    def __add__(self, other: "Log") -> "Log":
        new_log = Log(self.model, self.log + other.log)
        if new_log.length > self.prune_trigger:
            new_log.prune()
        self.log = new_log.log
        self.__save__()
        return self

    def __save__(self):
        save_dir = Path(os.getcwd()) / "saved_logs"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        if self.save_name is None:
            n_saved_logs = len([f for f in os.listdir(save_dir) if os.path.isfile(f)])
            self.save_name = f"log_{n_saved_logs}"
        save_path = save_dir / f"{self.save_name}.txt"
        pk.dump(self, open(save_path, "wb"))

    def load(self, file_path: Path):
        with open(file_path, "rb") as f:
            loaded_log = pk.load(f)
            self.model = loaded_log.model
            self.log = loaded_log.log
            self.prune_trigger = loaded_log.prune_trigger
            self.save_name = loaded_log.save_name
        print(f"Loaded log from {file_path}", Colors.alert)
        print()

    @property
    def length(self) -> int:
        enc = tiktoken.encoding_for_model(self.model)
        return sum([
            len(enc.encode(message.content))
            for message in self.log
        ])

    def __iter__(self):
        return iter(self.log)

    def print(self) -> None:
        if len(self.log) > 0:
            print(self, Colors.info)
        print(f"Log contains {self.length} tokens.", Colors.alert)
        print()

    def pop(self) -> Message:
        message = self.log.pop()
        self.__save__()
        return message

    def undo(self) -> None:
        while self.length > 0:
            message = self.pop()
            if message.role == "user":
                break
        print(f"Rewound to state of last message.", Colors.info)
        print()

    def clear(self):
        self.log = []
        print("Log cleared.", Colors.alert)
        print()
        self.__save__()

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
