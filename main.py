import argparse
from enum import Enum, auto
from typing import List
from dotenv import load_dotenv
import openai
import os
from pathlib import Path

from prompt_toolkit import PromptSession
from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Float, FloatContainer, HSplit, Layout, ScrollablePane, VSplit
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.shortcuts import input_dialog
from prompt_toolkit.widgets import (
    Button,
    Checkbox,
    Dialog,
    Label,
    TextArea,
)

from singularity.autocomplete import prompt
from singularity.code import show_code, summarize_codebase
from singularity.color_scheme import Colors
from singularity.llm import Message, llm_api
from singularity.logs import Log, get_title, print


load_dotenv()  # Load the OpenAI API key from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define command-line arguments
parser = argparse.ArgumentParser(description="Talk to LLM assistant")
# parser.add_argument("--model", type=str, default="gpt-4-32k", help="model to use")
# parser.add_argument("--model", type=str, default="gpt-4", help="model to use")
parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="model to use")
# parser.add_argument("--model", type=str, default="text-davinci-003", help="model to use")
parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature for generating text")
args = parser.parse_args()


class LoopStatus(Enum):
    Break = auto()
    Continue = auto()
    NoAction = auto()


def file_checkbox_dialog(files: List[str]):
    # TODO: get this working
    key_bindings = KeyBindings()

    @key_bindings.add('tab')
    def _(event):
        event.app.layout.focus_next()

    @key_bindings.add('s-tab')
    def _(event):
        event.app.layout.focus_previous()

    checkboxes = [(Checkbox(""), file) for file in files]
    check_actions = [Checkbox("Summary") for _ in range(len(files))]
    check_printouts = [Checkbox("Printout") for _ in range(len(files))]
    
    file_controls = [HSplit([Label(f, style='fg:red'), c], padding=1) for c, f in checkboxes]
    action_controls = [HSplit([Label("Summary"), a], padding=1) for a in check_actions]
    printout_controls = [HSplit([Label("Printout"), p], padding=1) for p in check_printouts]
    
    scrollable_body = ScrollablePane(
        # HSplit(
            # [
                # VSplit(file_controls, padding=1),
                # VSplit(action_controls, padding=1),
                # VSplit(printout_controls, padding=1)
            # ],
            # padding=1
        # )
        file_controls[0]
    )

    def ok_handler():
        selected_files = [
            f
            for a, p, f
            in zip(check_actions, check_printouts, files)
            if a.checked or p.checked
        ]
        summaries = [f for a, f in zip(check_actions, files) if a.checked]
        printouts = [f for p, f in zip(check_printouts, files) if p.checked]

        print(selected_files)
        print(summaries)
        print(printouts)
        app.exit()

    def cancel_handler():
        app.exit()

    ok_button = Button(text="OK", handler=ok_handler)
    cancel_button = Button(text="Cancel", handler=cancel_handler)
    dialog = Dialog(
        title="Select files to include",
        body=scrollable_body,
        buttons=[ok_button, cancel_button],
        width=None,
    )
    app = Application(
        layout=Layout(dialog),
        full_screen=False,
        key_bindings=key_bindings,
        mouse_support=True,
    )
    app.run()


def parse_user_input(user_input: str, log: Log) -> LoopStatus:
    if user_input == "/exit":
        return LoopStatus.Break
    # elif user_input == "/browse":
        # files = [os.path.join(r, f) for r, d, files in os.walk(os.getcwd()) for f in files]
        # file_checkbox_dialog(files)
        # return LoopStatus.Continue
    elif user_input == "/log":
        log.print()
        return LoopStatus.Continue
    elif user_input.startswith("/name"):
        name = " ".join(user_input.split()[1:])
        log.rename(name)
        return LoopStatus.Continue
    elif user_input == "/load":
        saved_logs = [f for f in os.listdir(log.save_dir)]
        logs_text = "\n".join([
            f"{i}: {get_title(log.save_dir / Path(f))}"
            for i, f in enumerate(saved_logs)
        ])  + "\n\nSelect saved log: "
        result = input_dialog(title="Select saved log", text=logs_text).run()
        if result is None:
            print("No log loaded.\n", Colors.alert)
        else:
            try:
                log.load(log.save_dir / saved_logs[int(result)])
            except Exception:
                print("Invalid selection.\n", Colors.alert)
        return LoopStatus.Continue
    elif user_input == "/clear":
        log.clear()
        return LoopStatus.Continue
    elif user_input.startswith("/code"):
        # TODO: switch to a toggle-based system where I flag what to keep in the preamble, and recalculate it every message
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
        print(f"Log contains {log.length} tokens.\n", Colors.info)
        return LoopStatus.Continue
    elif user_input.startswith("/show"):
        # TODO: switch to a toggle-based system where I flag what to keep in the preamble, and recalculate it every message
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
        log.undo()
        return LoopStatus.Continue
    elif user_input.startswith("/set_model"):
        model = user_input.split()[1]
        log.set_model(model)
        return LoopStatus.Continue
    elif user_input.startswith('/'):
        print(f"Invalid command.\n", Colors.info)
        return LoopStatus.Continue
    else:
        log.append(
            Message(
                role="user",
                content=user_input.strip(),
            )
        )
        return LoopStatus.NoAction


def parse_response(response: str, log: Log) -> LoopStatus:
    if response.startswith('/show'):
        user_input = prompt("Show assistant code? (y/n): ")
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
        f"You are now talking to the {args.model} model. "
        "Enter '/exit' to end the conversation.\n",
        Colors.info
    )
    log = Log(model=args.model, save_dir=Path("~/.singularity_logs"))
    while True:
        # no newline
        user_input = prompt("You: ")
        loop_status = parse_user_input(user_input, log)
        if loop_status == LoopStatus.Break:
            break
        elif loop_status == LoopStatus.Continue:
            continue
        response = llm_api(log.log, args.model, args.temperature)
        print(f"\nassistant: {response}\n", Colors.assistant, indent=2)
        log.append(
            Message(
                role="assistant",
                content=response.strip(),
            )
        )
        parse_response(response, log)


if __name__ == "__main__":
    main()
