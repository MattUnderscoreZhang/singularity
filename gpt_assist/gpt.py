import openai
from openai import error
from typing import Dict, List


# API for GPT
def gpt_api(messages: List[Dict], model: str, temperature: float) -> str:
    try:
        response = openai.ChatCompletion.create(
            model=model,
            messages=messages,
            temperature=temperature,
            frequency_penalty=0,
            presence_penalty=0
        )
        return response.choices[0].message.content
    except error.APIConnectionError as e:
        return str(e.user_message)
