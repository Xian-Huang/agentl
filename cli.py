from typing import Optional

from rich.prompt import Prompt
import typer

from .main import LLMChannel, ReActAgent

app = typer.Typer(no_args_is_help=True)


@app.callback()
def main() -> None:
    """Agentl command line interface."""


@app.command()
def chat(input_value: Optional[str] = typer.Argument(None), verbose: bool = typer.Option(False, "-v")):
    """Chat to agent"""

    channel = LLMChannel()
    agent = ReActAgent(channel=channel)

    if input_value:
        response = agent.chat(input=input_value, tools=None)
        print(response["content"])
        return

    while True:
        try:
            user_input = Prompt.ask("[green]You[/green]")
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ["exit", "q", "quit"]:
            break

        response = agent.chat(input=user_input, tools=None)
        print(response["content"])
