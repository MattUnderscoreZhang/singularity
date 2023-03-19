import ast
import os
from typing import Dict, List

from gpt_assist.gpt import start_chat
from gpt_assist.pprint import print


def __extract_public_functions(source: str) -> List[str]:
    tree = ast.parse(source, type_comments=True)
    fns = []
    for node in ast.iter_child_nodes(tree):
        if isinstance(node, ast.FunctionDef):
            if not node.name.startswith("_"):
                fn = f"{node.name}("  # ) for code completion
                for arg in node.args.args:
                    fn += f"{arg.arg}: {arg.type_comment}, "
                if fn.endswith(", "):
                    fn = fn[:-2]
                fn += ")"
                fns.append(fn)
    return fns


# Extract public functions and API from a code file
def summarize_code(filepath: str) -> str:
    with open(filepath, "r") as f:
        source = f.read()
    fns = __extract_public_functions(source)
    content = f"{filepath}:\n"
    for fn in fns:
        content += f"  {fn}\n"
    content += "\n"
    return content


# Feed a directory of code files to GPT
def feed_in_codebase(model: str, temperature: float) -> None:
    directory = os.getcwd()
    messages = [{
        "role": "user",
        "content": (
            "I'm going to summarize some code for you, then ask you questions afterwards."
            "Reply with 'ok' after you've read the summary."
        )
    }]
    codebase_summary = ""
    for root, _, filenames in os.walk(directory):
        if '.venv' in root or '__pycache__' in root: continue
        for filename in filenames:
            if not filename.endswith(".py"): continue
            filepath = os.path.join(root, filename)
            print(f"Summarizing file: {filepath}", "cyan")
            file_summary = summarize_code(filepath)
            codebase_summary += file_summary
    messages.append({
        "role": "user",
        "content": codebase_summary,
    })
    messages.append({
        "role": "assistant",
        "content": "ok",
    })
    for message in messages:
        print(message["role"])
        print(message["content"])
    start_chat(messages, model, temperature)


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
            print(f"Wrote generated code to {filepath}", "cyan")
    else:
        print("No code was saved.", "yellow")
