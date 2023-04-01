import builtins
from dataclasses import dataclass, field
import os
from pathlib import Path
import pickle as pk
from termcolor import colored
import textwrap
import tiktoken
from typing import Any, List, Optional

from singularity.color_scheme import Colors
from singularity.llm import Message, llm_api


@dataclass
class Log:
    model: str
    log: List[Message] = field(default_factory=list)
    prune_trigger: int = 3500
    after_prune_threshold: int = 1500
    filename: Optional[str] = None
    title: Optional[str] = None

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
        save_dir = Path(os.getcwd()) / "singularity_logs"
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
        if self.filename is None:
            n_saved_logs = len([f for f in os.listdir(save_dir)])
            self.filename = f"log_{n_saved_logs}"
        save_path = save_dir / f"{self.filename}.txt"
        if self.title is None:
            self.title = self.filename
        pk.dump(self, open(save_path, "wb"))

    def rename(self, new_name: str) -> None:
        self.title = new_name
        print(f"Renamed log to {new_name}\n", Colors.alert)
        self.__save__()

    def set_model(self, new_model: str) -> None:
        self.model = new_model
        print(f"You are now talking to the {self.model} model.\n")
        self.__save__()

    def load(self, filepath: Path):
        with open(filepath, "rb") as f:
            loaded_log = pk.load(f)
            self.model = loaded_log.model
            self.log = loaded_log.log
            self.prune_trigger = loaded_log.prune_trigger
            self.after_prune_threshold = loaded_log.after_prune_threshold
            self.filename = loaded_log.filename
            self.title = loaded_log.title
        print(f"Loaded '{loaded_log.title}'", Colors.alert)
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
        print("Pruning log...", Colors.alert)
        try:
            summary = "Summary of chat: " + llm_api(messages, self.model, 1)
            new_log = [
                message
                for message in self.log
                if message.persist
            ] + [Message(role="assistant", content=summary)]
            enc = tiktoken.encoding_for_model(self.model)
            new_log_length = sum([
                len(enc.encode(message.content))
                for message in new_log
            ])
            n_messages_kept = 0
            messages.pop()
            kept_messages_length = len(enc.encode(messages[-1].content))
            while kept_messages_length + new_log_length < self.after_prune_threshold:
                n_messages_kept += 1
                kept_messages_length += len(enc.encode(messages[-n_messages_kept-1].content))
            min_messages_kept = 3
            new_log += messages[-max(n_messages_kept, min_messages_kept):]
            self.log = new_log
            print("Pruning successful.\n", Colors.alert)
        except Exception:
            print("Failed to prune log.\n", Colors.alert)


def get_title(filepath: Path) -> str:
    with open(filepath, "rb") as f:
        loaded_log = pk.load(f)
        return loaded_log.title


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
