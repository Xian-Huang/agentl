from typing import Any, Protocol


class ChatChannel(Protocol):
    """The model boundary required by ReActAgent."""

    def send_request(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ) -> dict[str, Any]: ...
