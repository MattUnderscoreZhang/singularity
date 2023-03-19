import ast
import os
from pathlib import Path
from typing import List

from singularity.color_scheme import Colors
from singularity.logs import Log, print


def show_code(directory: Path, rel_filepath: Path, cls_name: str, fn_name: str) -> str:
    try:
        with open(directory / rel_filepath) as f:
            file_contents = f.read()
            root = ast.parse(file_contents)
    except IsADirectoryError:
        print(f"Path is a directory: {rel_filepath}\n", Colors.info)
        return ""
    except FileNotFoundError:
        print(f"File not found: {rel_filepath}\n", Colors.info)
        return ""

    if cls_name == "" and fn_name == "":
        return file_contents
    elif cls_name == "":
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


def __get_ast_value(node: ast.AST) -> str:
    if isinstance(node, ast.Constant):
        if isinstance(node.value, str):
            return f"'{node.value}'"
        else:
            return node.value
    elif isinstance(node, ast.Call):
        func = node.func
        if isinstance(func, ast.Name):
            return func.id + "()"
    return ast.dump(node)


def __get_ast_function(node: ast.FunctionDef, docstrings: bool, tabs: int) -> str:
    # TODO: add type annotations and default values
    func_args = [arg.arg for arg in node.args.args]
    if docstrings:
        func_doc = ast.get_docstring(node) or ""
        if func_doc != "":
            func_doc = f"\n{func_doc}".replace("\n", "\n" + "\t" * tabs)
    else:
        func_doc = ""
    return "\t" * tabs + f"{node.name}({', '.join(func_args)}){func_doc}"


def __get_ast_members(node: ast.ClassDef, tabs: int) -> List[str]:
    member_strs = []
    for item in node.body:
        if isinstance(item, ast.Assign):
            for target in item.targets:
                if not isinstance(target, ast.Name):
                    continue
                name = target.id
                if item.value is None:
                    member_strs.append("\t" * tabs + name)
                else:
                    value = __get_ast_value(item.value)
                    member_strs.append("\t" * tabs + f"{name} = {value}")
        elif isinstance(item, ast.AnnAssign):
            if (
                not isinstance(item.target, ast.Name)
                or not isinstance(item.annotation, ast.Name)
            ):
                continue
            name = item.target.id
            type = item.annotation.id
            if item.value is None:
                member_strs.append("\t" * tabs + f"{name}: {type}")
            else:
                value = __get_ast_value(item.value)
                member_strs.append("\t" * tabs + f"{name}: {type} = {value}")
    return member_strs


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

    code_summary = [f"{rel_filepath}:"]
    # Classes
    for node in root.body:
        if isinstance(node, ast.ClassDef) and not node.name.startswith("_"):
            if docstrings:
                class_doc = ast.get_docstring(node) or ""
                if class_doc != "":
                    class_doc = f"\n{class_doc}".replace("\n", "\n\t")
            else:
                class_doc = ""
            bases = [base.id for base in node.bases if isinstance(base, ast.Name)]
            bases_str = "" if len(bases) == 0 else f"({', '.join(bases)})"
            decorators = [f"@{d.id}" for d in node.decorator_list if isinstance(d, ast.Name)]
            dec_str = "" if len(decorators) == 0 else '\t' + '\n\t'.join(decorators) + '\n'
            code_summary.append(f"{dec_str}\tclass {node.name}{bases_str}:{class_doc}")
            # Members
            code_summary += __get_ast_members(node, tabs=2)
            # Methods
            code_summary += [
                __get_ast_function(item, docstrings, tabs=2)
                for item in node.body
                if isinstance(item, ast.FunctionDef)
                and not item.name.startswith("_")
            ]
    # Functions
    code_summary += [
        __get_ast_function(node, docstrings, tabs=1)
        for node in root.body
        if isinstance(node, ast.FunctionDef)
        and not node.name.startswith("_")
    ]
    return "\n".join(code_summary) + "\n\n"


def summarize_codebase(docstrings: bool = False) -> str:
    """
    Summarizes all public functions and classes defined in the current directory.

    Args:
        docstrings: Whether to include docstrings in the summary.

    Returns:
        A formatted summary string of all code, with optional docstrings.
    """
    directory = Path(os.getcwd())
    codebase_summary = ""
    for root, _, filenames in os.walk(directory):
        if '.venv' in root or '__pycache__' in root: continue
        for filename in filenames:
            if not filename.endswith(".py"): continue
            filepath = os.path.join(root, filename)
            rel_filepath = Path(filepath).resolve().relative_to(directory)
            print(f"Summarizing file: {rel_filepath}", Colors.info)
            file_summary = summarize_code(directory, rel_filepath, docstrings)
            codebase_summary += file_summary
    return codebase_summary


# TODO: work in progress
def suggest_code(log: Log, model: str, temperature: float) -> None:
    print(f"Assistant is suggesting code based on your conversation with {model}.\n", Colors.info)
    generated_code = generate_code(log, model, temperature)
    print(f"Assistant suggested the following code:\n{generated_code}\n", Colors.info)
    response = input("Would you like to accept this code? (y/n): ").strip().lower()
    if response == "y":
        filename = input("Please enter a filename for this code (include the .py extension): ").strip()
        filepath = os.path.join(os.getcwd(), filename)
        with open(filepath, "w") as f:
            f.write(generated_code)
            print(f"Wrote generated code to {filepath}", Colors.info)
    else:
        print("No code was saved.", Colors.info)


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
