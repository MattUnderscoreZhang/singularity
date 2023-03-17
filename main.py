import os
from typing import Dict, List
from dotenv import load_dotenv
import openai
import argparse
from termcolor import colored
import textwrap


load_dotenv()  # Load the OpenAI API key from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define command-line arguments
parser = argparse.ArgumentParser(description="Talk to GPT")
# parser.add_argument("--model", type=str, default="gpt-4", help="GPT model to use")
parser.add_argument("--model", type=str, default="gpt-3.5-turbo", help="GPT model to use")
parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature for generating text")
args = parser.parse_args()


def pretty_print(content, color, indent=0):
    wrapper = textwrap.TextWrapper(initial_indent=" " * indent, subsequent_indent=" " * indent, width=80)
    parts = content.split("```")
    for i, part in enumerate(parts):
        if i % 2 == 0: print(colored(wrapper.fill(part), color))
        else: print(part)


# API for GPT
def talk_to_gpt(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


# Start a conversation with GPT
def start_conversation(messages: List[Dict[str, str]], model: str, temperature: float) -> None:
    print(f"You are now talking to the {model} GPT model. Enter '/exit' to end the conversation.\n")
    while True:
        user_input = input(colored("You: ", "green"))
        if user_input == "/exit":
            break
        messages.append({"role": "user", "content": user_input.strip()})
        response = talk_to_gpt(messages, model, temperature)
        pretty_print(f"GPT: {response}", "yellow", indent=2)
        messages.append({"role": "assistant", "content": response.strip()})


# Feed a directory of code files to GPT
def feed_in_codebase(model: str, temperature: float) -> None:
    directory = os.getcwd()
    messages = [{
        "role": "user",
        "content": "I'm going to give you a set of Python files, then ask you questions afterwards. Simply respond to each new file with 'ok' until I finish."
    }]
    for filename in os.listdir(directory):
        filepath = os.path.join(directory, filename)
        if os.path.isfile(filepath) and filepath.endswith(".py"):
            pretty_print(f"Reading file: {filepath}", "cyan")
            with open(filepath, "r") as f:
                code = f.read()
                messages.append({
                    "role": "user",
                    "content": f"Here is the code for {filename}:\n\n" + code,
                })
                messages.append({
                    "role": "assistant",
                    "content": "ok",
                })
    suggest_code(messages, model, temperature)


# TODO: work in progress
def generate_code(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    response = openai.Completion.create(
        engine=model,
        prompt='\n'.join([m['content'] for m in messages]),
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=temperature,
    )
    return response.choices[0].text.strip()


# TODO: work in progress
def suggest_code(messages: List[Dict[str, str]], model: str, temperature: float) -> None:
    print(f"GPT is suggesting code based on your conversation with {model}.\n")
    generated_code = generate_code(messages, model, temperature)
    print(f"GPT suggested the following code:\n{generated_code}\n")
    response = input("Would you like to accept this code? (y/n): ").strip().lower()
    if response == "y":
        filename = input("Please enter a filename for this code (include the .py extension): ").strip()
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, "w") as f:
            f.write(generated_code)
            pretty_print(f"Wrote generated code to {filepath}", "cyan")
    else:
        pretty_print("No code was saved.", "yellow")


if __name__ == "__main__":
    pretty_print("Welcome to the GPT command-line interface!", "cyan")
    while True:
        print(
            "Please choose an option:\n"
            "1. Start a new chat\n"
            "2. Work in current codebase\n"
            "3. Exit"
        )
        choice = input(colored("Your choice (1/2/3): ", "green"))
        if choice == "1":
            start_conversation([], args.model, args.temperature)
        elif choice == "2":
            feed_in_codebase(model='code-davinci-002', temperature=args.temperature)
        elif choice == "3":
            break
        else:
            pretty_print("Invalid choice. Please choose again.", "red")
