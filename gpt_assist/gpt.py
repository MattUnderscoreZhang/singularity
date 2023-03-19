import openai
from termcolor import colored
from typing import Dict, List

from gpt_assist.pprint import print


# API for GPT
def __gpt_api(messages: List[Dict[str, str]], model: str, temperature: float) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


# Start a conversation with GPT
def start_chat(messages: List[Dict[str, str]], model: str, temperature: float) -> None:
    print(f"You are now talking to the {model} GPT model. Enter '/exit' to end the conversation.\n")
    while True:
        user_input = input(colored("You: ", "green"))
        if user_input == "/exit":
            break
        messages.append({"role": "user", "content": user_input.strip()})
        response = __gpt_api(messages, model, temperature)
        print(f"GPT: {response}", "yellow", indent=2)
        messages.append({"role": "assistant", "content": response.strip()})
