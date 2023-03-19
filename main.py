import argparse
from dotenv import load_dotenv
import openai
import os
from termcolor import colored
from typing import Dict, List

from gpt_assist.code import feed_in_codebase
from gpt_assist.logs import Log, print
from gpt_assist.gpt import start_chat


load_dotenv()  # Load the OpenAI API key from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define command-line arguments
parser = argparse.ArgumentParser(description="Talk to GPT")
# parser.add_argument("--model", type=str, default="gpt-4", help="GPT model to use")
parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="GPT model to use")
parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature for generating text")
args = parser.parse_args()


# TODO: work in progress
def generate_code(log: Log, model: str, temperature: float) -> str:
    response = openai.Completion.create(
        engine=model,
        prompt='\n'.join([m['content'] for m in log]),
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=temperature,
    )
    return response.choices[0].text.strip()


def main():
    print("Welcome to the GPT command-line interface!", "cyan")
    while True:
        print(
            "Please choose an option:\n"
            "1. Start a new chat\n"
            "2. Work in current codebase\n"
            "3. Exit"
        )
        choice = input(colored("Your choice (1/2/3): ", "green"))
        print()
        if choice == "1":
            start_chat([], args.model, args.temperature)
        elif choice == "2":
            feed_in_codebase(model=args.model, temperature=args.temperature)
        elif choice == "3":
            break
        else:
            print("Invalid choice. Please choose again.", "red")


if __name__ == "__main__":
    main()
