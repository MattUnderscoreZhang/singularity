from dataclasses import dataclass
import openai
from openai import error
from time import sleep, time
from typing import List


@dataclass
class Message:
    role: str
    content: str
    persist: bool = False

    def __str__(self) -> str:
        return f"{self.role}: {self.content}"


# Rate limiter
last_call: float = time()


# API for GPT
def gpt_api(messages: List[Message], model: str, temperature: float) -> str:
    global last_call
    if time() - last_call < 1:
        sleep(1)
        last_call = time()
    try:
        if model in [
            "gpt-4",
            "gpt-4-0314",
            "gpt-4-32k",
            "gpt-4-32k-0314",
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-0301",
        ]:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {
                        "role": m.role,
                        "content": m.content
                    }
                    for m in messages
                ],
                temperature=temperature,
                frequency_penalty=0,
                presence_penalty=0
            )
            return response.choices[0].message.content
        elif model in [
            "text-davinci-003",
            "text-davinci-002",
            "text-curie-001",
            "text-babbage-001",
            "text-ada-001",
            "davinci",
            "curie",
            "babbage",
            "ada",
        ]:
            response = openai.Completion.create(
                model=model,
                prompt="\n".join([f"{m.role}: {m.content}" for m in messages]) + "assistant: ",
                temperature=temperature,
                max_tokens=100,
                top_p=1,
                frequency_penalty=0,
                presence_penalty=0,
            )
            return response.choices[0].text
        # TODO: add code completion
        # https://platform.openai.com/docs/guides/code/editing-code
        else:
            return str("Unsupported model.")
    except error.APIConnectionError as e:
        return str(e.user_message)


# Current backend
llm_api = gpt_api
