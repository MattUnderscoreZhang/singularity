import argparse
from dotenv import load_dotenv
import openai
import os
from pathlib import Path
from termcolor import colored

from gpt_assist.code import load_code, summarize_codebase
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


def main():
    print(
        f"You are now talking to the {args.model} GPT model. "
        "Enter '/exit' to end the conversation or '/help' for help.\n"
    )
    log = Log()
    while True:
        user_input = input(colored("You: ", "green"))
        if user_input == "/exit":
            break
        elif user_input == "/help":
            print(
                "/exit: end the conversation\n"
                "/help: show this help message\n"
                "/log: show the conversation log\n"
                "/code: upload codebase from current directory\n"
                "/upload: upload code (relative filepath)\n"
            )
            continue
        elif user_input == "/log":
            print(log)
            print(f"Log contains {log.length} tokens.")
            continue
        elif user_input.startswith("/code"):
            message = summarize_codebase()
            log += Log([message])
            print(f"Log contains {log.length} tokens.")
            print()
            print(log)
            continue
        elif user_input.startswith("/upload"):
            directory = Path(os.getcwd())
            rel_filepath = Path(user_input.split()[1])
            log.append(
                Message(
                    role="user",
                    content=load_code(directory, rel_filepath)
                )
            )
        else:
            log.append(
                Message(
                    role="user",
                    content=user_input.strip(),
                )
            )
        response = gpt_api(log.to_messages(), args.model, args.temperature)
        print(f"\nGPT: {response}\n", "yellow", indent=2)
        log.append(
            Message(
                role="assistant",
                content=response.strip(),
            )
        )




if __name__ == "__main__":
    main()
