import os
from dotenv import load_dotenv
import openai
import argparse


load_dotenv()  # Load the OpenAI API key from a .env file
openai.api_key = os.getenv("OPENAI_API_KEY")


# Define command-line arguments
parser = argparse.ArgumentParser(description="Talk to GPT-4")
parser.add_argument("--prompt", type=str, default="", help="Prompt to start the conversation")
parser.add_argument("--model", type=str, default="gpt-4", help="GPT-4 model to use")
parser.add_argument("--temperature", type=float, default=1, help="Sampling temperature for generating text")
args = parser.parse_args()


# Start the conversation
def talk_to_gpt(prompt: str, model: str, temperature: float) -> str:
    response = openai.ChatCompletion.create(
        model=model,
        messages=[
            {"role": "user", "content": prompt},
        ],
        temperature=temperature,
        frequency_penalty=0,
        presence_penalty=0
    )
    return response.choices[0].message.content


if __name__ == "__main__":
    prompt = args.prompt
    model = args.model
    temperature = args.temperature

    print(f"You are now talking to the {model} GPT-4 model. Enter '/exit' to end the conversation.\n")

    while True:
        user_input = input("You: ")
        if user_input == "/exit":
            break
        prompt += user_input.strip()
        message = talk_to_gpt(prompt, model, temperature)
        print(f"GPT-4: {message}")
