import ast
import os
from pathlib import Path

from gpt_assist.gpt import start_chat
from gpt_assist.logs import Log, Message, print


def summarize_code(filepath: str, directory: str):
    """
    Given a filepath, returns a formatted string that summarizes all public functions 
    and classes defined in the file. Each function and class is described with its name, 
    arguments, and docstring, and the string is separated with newlines.
    
    Args:
        filepath: The path of the file to summarize.
    
    Returns:
        A formatted summary string of all public functions and classes, with docstrings.
    """
    with open(filepath) as f:
        root = ast.parse(f.read())

    dir_filepath = Path(directory).resolve()
    rel_filepath = Path(filepath).resolve().relative_to(dir_filepath)

    funcs_and_classes = [f"{rel_filepath}:"]
    for node in root.body:
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_"):
                continue
            func_args = [arg.arg for arg in node.args.args]
            func_doc = ast.get_docstring(node) or ""
            if func_doc != "":
                func_doc = f"\n'''\n{func_doc}\n'''".replace("\n", "\n\t")
            funcs_and_classes.append(f"\t{node.name}({', '.join(func_args)}){func_doc}")
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            class_doc = ast.get_docstring(node) or ""
            if class_doc != "":
                class_doc = f"\n{class_doc}".replace("\n", "\n\t")
            funcs_and_classes.append(f"\t{node.name}:{class_doc}")
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith("_"):
                        continue
                    func_args = ["self"] + [arg.arg for arg in item.args.args[1:]]
                    func_doc = ast.get_docstring(item) or ""
                    if func_doc != "":
                        func_doc = f"\n{func_doc}".replace("\n", "\n\t\t")
                    funcs_and_classes.append(
                        f"\t\t{item.name}({', '.join(func_args)}){func_doc}"
                    )

    return "\n".join(funcs_and_classes) + "\n\n"


# Feed a directory of code files to GPT
def feed_in_codebase(model: str, temperature: float) -> None:
    directory = os.getcwd()
    log = Log([
        Message(
            role="user",
            content=(
                "I'm going to summarize some code for you, then ask you questions afterwards. "
                "If during conversation I refer to specific code that you want to see, please "
                "ask me to show it to you."
            ),
            preamble=True,
        )
    ])
    codebase_summary = ""
    for root, _, filenames in os.walk(directory):
        if '.venv' in root or '__pycache__' in root: continue
        for filename in filenames:
            if not filename.endswith(".py"): continue
            filepath = os.path.join(root, filename)
            print(f"Summarizing file: {filepath}", "cyan")
            file_summary = summarize_code(filepath, directory)
            codebase_summary += file_summary
    log.append(
        Message(
            role="user",
            content=codebase_summary,
            preamble=True,
        )
    )
    print(log)
    start_chat(log, model, temperature)


# TODO: work in progress
def suggest_code(log: Log, model: str, temperature: float) -> None:
    print(f"GPT is suggesting code based on your conversation with {model}.\n")
    generated_code = generate_code(log, model, temperature)
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
