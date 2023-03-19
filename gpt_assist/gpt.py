import openai
from termcolor import colored
from typing import Dict, List

from gpt_assist.logs import Log, Message, print


# API for GPT
def __gpt_api(log: Log, model: str, temperature: float) -> str:
    messages = [
        {
            "role": m.role,
            "content": m.content
        }
        for m in log
    ]
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


# Start a conversation with GPT
def start_chat(log: Log, model: str, temperature: float) -> None:
    print(
        f"You are now talking to the {model} GPT model. "
        "Enter '/exit' to end the conversation.\n"
    )
    while True:
        user_input = input(colored("You: ", "green"))
        if user_input == "/exit":
            break
        log.append(
            Message(
                role="user",
                content=user_input.strip(),
            )
        )
        response = __gpt_api(log, model, temperature)
        print(f"\nGPT: {response}\n", "yellow", indent=2)
        log.append(
            Message(
                role="assistant",
                content=response.strip(),
            )
        )
