import argparse
from enum import Enum, auto
from dotenv import load_dotenv
import openai
import os
from pathlib import Path

from gpt_assist.autocomplete import prompt
from gpt_assist.code import show_code, summarize_codebase
from gpt_assist.color_scheme import Colors
from gpt_assist.gpt import gpt_api
from gpt_assist.logs import Log, Message, print


load_dotenv()  # Load the OpenAI API key from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define command-line arguments
parser = argparse.ArgumentParser(description="Talk to GPT")
# parser.add_argument("--model", type=str, default="gpt-4", help="GPT model to use")
parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="GPT model to use")
parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature for generating text")
args = parser.parse_args()


class LoopStatus(Enum):
    Break = auto()
    Continue = auto()
    NoAction = auto()


def parse_user_input(user_input: str, log: Log) -> LoopStatus:
    if user_input == "/exit":
        return LoopStatus.Break
    elif user_input == "/log":
        print(log, Colors.info)
        print(f"Log contains {log.length} tokens.", Colors.alert)
        print()
        return LoopStatus.Continue
    elif user_input == "/clear":
        log.log = []
        print("Log cleared.", Colors.alert)
        print()
        return LoopStatus.Continue
    elif user_input.startswith("/code"):
        codebase_summary = summarize_codebase()
        message = Message(
            role="user",
            content="```\n" + codebase_summary + "```",
            # content=(
                # "```\n" + codebase_summary + "```" +
                # "This is a high-level codebase overview. You will need to see code in more detail "
                # "in order to answer questions. To do so, use the following command. Do not include "
                # "any additional text or quotes when running the command.\n\n"
                # "/show <filepath>:<class>:<function>\n\n"
                # "Examples:\n"
                # "/show main.py:Dog:bark\n"
                # "/show main.py::list_animals\n"
                # "/show main.py:Cat:\n"
            # ),
            persist=True,
        )
        log.append(message)
        print(f"Log contains {log.length} tokens.", Colors.info)
        print()
        return LoopStatus.Continue
    elif user_input.startswith("/show"):
        directory = Path(os.getcwd())
        show_args = user_input.split()[1].split(':')
        code = (
            show_code(directory, Path(show_args[0]), show_args[1], show_args[2])
            if len(show_args) == 3
            else show_code(directory, Path(show_args[0]), "", "")
        )
        if code != "":
            message = Message(
                role="user",
                content="```\n" + code + "```",
            )
            log.append(message)
            print(message, Colors.info)
        return LoopStatus.Continue
    elif user_input == "/undo":
        while log.length > 0:
            message = log.pop()
            if message.role == "user":
                break
        print(f"Rewound to state of last message.", Colors.info)
        print()
        return LoopStatus.Continue
    elif user_input.startswith('/'):
        print(f"Invalid command.", Colors.info)
        print()
        return LoopStatus.Continue
    else:
        log.append(
            Message(
                role="user",
                content=user_input.strip(),
            )
        )
        return LoopStatus.NoAction


def parse_gpt_response(response: str, log: Log) -> LoopStatus:
    if response.startswith('/show'):
        user_input = prompt("Show GPT code? (y/n): ")
        if user_input.lower() == "y":
            directory = Path(os.getcwd())
            show_args = response.split()[1].split(':')
            code = show_code(directory, Path(show_args[0]), show_args[1], show_args[2])
            print(code, Colors.info)
            log.append(
                Message(
                    role="user",
                    content=code,
                )
            )
        else:
            log.append(
                Message(
                    role="user",
                    content="Access denied.",
                )
            )
        return LoopStatus.NoAction
    else:
        return LoopStatus.NoAction


def main():
    print(
        f"You are now talking to the {args.model} GPT model.\n"
        "Enter '/exit' to end the conversation.\n",
        Colors.info
    )
    log = Log(args.model)
    while True:
        # no newline
        user_input = prompt("You: ")
        loop_status = parse_user_input(user_input, log)
        if loop_status == LoopStatus.Break:
            break
        elif loop_status == LoopStatus.Continue:
            continue
        response = gpt_api(log.to_messages(), args.model, args.temperature)
        print(f"\nGPT: {response}\n", Colors.gpt, indent=2)
        log.append(
            Message(
                role="assistant",
                content=response.strip(),
            )
        )
        parse_gpt_response(response, log)


if __name__ == "__main__":
    main()
