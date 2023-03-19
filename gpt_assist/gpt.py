import openai
from typing import Dict, List


# API for GPT
def gpt_api(messages: List[Dict], model: str, temperature: float) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=messages,
        temperature=temperature,
        frequency_penalty=0,
        presence_penalty=0
    )
    # response.usage.total_tokens
    return response.choices[0].message.content
