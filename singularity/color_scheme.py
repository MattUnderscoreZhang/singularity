from prompt_toolkit.styles import Style
from typing import NamedTuple


class Colors(NamedTuple):
    info = "blue"
    assistant = "magenta"
    alert = "yellow"
    warning = "red"
    code = "cyan"


prompt_style = Style.from_dict(
    {
        # Default style.
        "": "#ffdaac",
        # Prompt.
        "username": "#884444 italic",
        "at": "#00aa00",
        "colon": "#00aa00",
        "pound": "#00aa00",
        "host": "#000088 bg:#aaaaff",
        "path": "#884444 underline",
        # Make a selection reverse/underlined.
        # (Use Control-Space to select.)
        "selected-text": "reverse underline",
    }
)
