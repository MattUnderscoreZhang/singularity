import glob
from prompt_toolkit.completion import CompleteEvent, Completer, Completion
from prompt_toolkit.document import Document
from prompt_toolkit import shortcuts

from singularity.color_scheme import prompt_style


commands = [
    ("/exit", "end the conversation"),
    ("/log", "show the conversation log"),
    ("/name", "[name] change the conversation name"),
    ("/load", "load conversation log from file"),
    ("/clear", "clear log"),
    ("/code", "upload codebase from current directory"),
    ("/show", "[filepath]:[optional-class]:[optional-function] show code snippet"),
    ("/undo", "delete last user message"),
]


class CommandCompleter(Completer):
    def get_completions(self, document: Document, complete_event: CompleteEvent):
        text_before_cursor = document.text_before_cursor
        words_before_cursor = text_before_cursor.split()
        current_word = document.get_word_under_cursor()

        # Suggest filepaths if "/show" is typed
        if (
            (
                (len(words_before_cursor) == 1 and current_word == "")
                or (len(words_before_cursor) == 2)
            )
            and words_before_cursor[0] == "/show"
        ):
            path = "".join(words_before_cursor[1:])
            suggestions = [
                Completion(
                    suggestion,
                    start_position=-len(path),
                    display=suggestion,
                    display_meta="",
                ) for suggestion in glob.glob(path + "*")
            ]
            for suggestion in suggestions:
                yield suggestion

        # Command suggestions
        elif len(words_before_cursor) == 1 and words_before_cursor[0].startswith('/'):
            for command, description in [
                c for c in commands
                if c[0].startswith(words_before_cursor[-1])
            ]:
                yield Completion(
                    command,
                    start_position=-len(current_word)-1,
                    display=command,
                    display_meta=description,
                )


def prompt(prompt_str: str) -> str:
    return shortcuts.prompt(prompt_str, style=prompt_style, completer=CommandCompleter())
