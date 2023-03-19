import ast
import os
from pathlib import Path

from gpt_assist.color_scheme import colors
from gpt_assist.logs import Log, Message, print


def show_code(directory: Path, rel_filepath: Path, cls_name: str, fn_name: str) -> str:
    with open(directory / rel_filepath) as f:
        root = ast.parse(f.read())

    if cls_name == "":
        for node in root.body:
            if isinstance(node, ast.FunctionDef):
                if node.name == fn_name:
                    return ast.unparse(node)
    else:
        for node in root.body:
            if isinstance(node, ast.ClassDef):
                if node.name == cls_name:
                    if fn_name == "":
                        return ast.unparse(node)
                    for subnode in node.body:
                        if isinstance(subnode, ast.FunctionDef):
                            if subnode.name == fn_name:
                                return ast.unparse(subnode)
    return "Code not found."


def summarize_code(directory: Path, rel_filepath: Path, docstrings: bool = False) -> str:
    """
    Given a filepath, returns a formatted string that summarizes all public functions 
    and classes defined in the file. Each function and class is described with its name, 
    arguments, and docstring, and the string is separated with newlines.
    
    Args:
        rel_filepath: The path of the file to summarize relative to the root directory.
        directory: The root directory.
    
    Returns:
        A formatted summary string of all public functions and classes, with docstrings.
    """
    with open(directory / rel_filepath) as f:
        root = ast.parse(f.read())

    funcs_and_classes = [f"{rel_filepath}:"]
    for node in root.body:
        if isinstance(node, ast.FunctionDef):
            if node.name.startswith("_"):
                continue
            func_args = [arg.arg for arg in node.args.args]
            if docstrings:
                func_doc = ast.get_docstring(node) or ""
                if func_doc != "":
                    func_doc = f"\n'''\n{func_doc}\n'''".replace("\n", "\n\t")
            else:
                func_doc = ""
            funcs_and_classes.append(f"\t{node.name}({', '.join(func_args)}){func_doc}")
        elif isinstance(node, ast.ClassDef):
            if node.name.startswith("_"):
                continue
            if docstrings:
                class_doc = ast.get_docstring(node) or ""
                if class_doc != "":
                    class_doc = f"\n{class_doc}".replace("\n", "\n\t")
            else:
                class_doc = ""
            funcs_and_classes.append(f"\t{node.name}:{class_doc}")
            for item in node.body:
                if isinstance(item, ast.FunctionDef):
                    if item.name.startswith("_"):
                        continue
                    func_args = ["self"] + [arg.arg for arg in item.args.args[1:]]
                    if docstrings:
                        func_doc = ast.get_docstring(item) or ""
                        if func_doc != "":
                            func_doc = f"\n{func_doc}".replace("\n", "\n\t\t")
                    else:
                        func_doc = ""
                    funcs_and_classes.append(
                        f"\t\t{item.name}({', '.join(func_args)}){func_doc}"
                    )

    return "\n".join(funcs_and_classes) + "\n\n"


# Feed a directory of code files to GPT
def summarize_codebase() -> str:
    directory = Path(os.getcwd())
    codebase_summary = ""
    for root, _, filenames in os.walk(directory):
        if '.venv' in root or '__pycache__' in root: continue
        for filename in filenames:
            if not filename.endswith(".py"): continue
            filepath = os.path.join(root, filename)
            rel_filepath = Path(filepath).resolve().relative_to(directory)
            print(f"Summarizing file: {rel_filepath}", colors.info)
            file_summary = summarize_code(directory, rel_filepath)
            codebase_summary += file_summary
    return codebase_summary


# TODO: work in progress
def suggest_code(log: Log, model: str, temperature: float) -> None:
    print(f"GPT is suggesting code based on your conversation with {model}.\n", colors.info)
    generated_code = generate_code(log, model, temperature)
    print(f"GPT suggested the following code:\n{generated_code}\n", colors.info)
    response = input("Would you like to accept this code? (y/n): ").strip().lower()
    if response == "y":
        filename = input("Please enter a filename for this code (include the .py extension): ").strip()
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, "w") as f:
            f.write(generated_code)
            print(f"Wrote generated code to {filepath}", colors.info)
    else:
        print("No code was saved.", colors.info)


# TODO: work in progress
def generate_code(log: Log, model: str, temperature: float) -> str:
    response = openai.Completion.create(
        engine=model,
        prompt='\n'.join([m.content for m in log]),
        max_tokens=1024,
        n=1,
        stop=None,
        temperature=temperature,
    )
    return response.choices[0].text.strip()
