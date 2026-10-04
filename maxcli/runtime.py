"""Small, shared command contract for humans and scripts."""
import builtins
from contextvars import ContextVar

NON_INTERACTIVE = ContextVar("maxcli_non_interactive", default=False)


class CommandError(Exception):
    """An actionable user error, displayed without a traceback."""


def require_interactive() -> None:
    if NON_INTERACTIVE.get():
        raise CommandError("This command requires input. Supply explicit arguments or run in an interactive terminal.")


def prompt_input(prompt: str = "") -> str:
    require_interactive()
    return builtins.input(prompt)
