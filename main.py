import argparse
from enum import Enum, auto
from dotenv import load_dotenv
import openai
import os
from pathlib import Path
from termcolor import colored

from gpt_assist.code import show_code, summarize_codebase
from gpt_assist.color_scheme import colors
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
    elif user_input == "/help":
        print(
            "/exit: end the conversation\n"
            "/help: show this help message\n"
            "/log: show the conversation log\n"
            "/clear: clear log\n"
            "/code: upload codebase from current directory\n"
            "/show <filepath>:<class>:<function> show code snippet\n"
                "    Examples:\n"
                "    /show main.py:Dog:bark\n"
                "    /show main.py::list_animals\n"
                "    /show main.py:Cat:\n"
            "/back: rewind chat to previous user message\n",
            colors.info
        )
        return LoopStatus.Continue
    elif user_input == "/log":
        print(log, colors.info)
        print(f"Log contains {log.length} tokens.", colors.alert)
        print()
        return LoopStatus.Continue
    elif user_input == "/clear":
        log.log = []
        print("Log cleared.", colors.alert)
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
        print(f"Log contains {log.length} tokens.", colors.info)
        print()
        return LoopStatus.Continue
    elif user_input.startswith("/show"):
        directory = Path(os.getcwd())
        show_args = user_input.split()[1].split(':')
        code = show_code(directory, Path(show_args[0]), show_args[1], show_args[2])
        message = Message(
            role="user",
            content="```\n" + code + "```",
        )
        log.append(message)
        print(message, colors.info)
        return LoopStatus.Continue
    elif user_input == "/back":
        while log.length > 0:
            message = log.pop()
            if message.role == "user":
                break
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
        user_input = input(colored("Show GPT code? (y/n): ", colors.user))
        if user_input.lower() == "y":
            directory = Path(os.getcwd())
            show_args = response.split()[1].split(':')
            code = show_code(directory, Path(show_args[0]), show_args[1], show_args[2])
            print(code, colors.info)
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
        f"You are now talking to the {args.model} GPT model. "
        "Enter '/exit' to end the conversation or '/help' for help.\n",
        colors.info
    )
    log = Log(args.model)
    while True:
        user_input = input(colored("You: ", colors.user))
        loop_status = parse_user_input(user_input, log)
        if loop_status == LoopStatus.Break:
            break
        elif loop_status == LoopStatus.Continue:
            continue
        response = gpt_api(log.to_messages(), args.model, args.temperature)
        print(f"\nGPT: {response}\n", colors.gpt, indent=2)
        log.append(
            Message(
                role="assistant",
                content=response.strip(),
            )
        )
        parse_gpt_response(response, log)


if __name__ == "__main__":
    main()
