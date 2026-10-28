import json
import os
import re
from typing import Any
import httpx
from .provider import ChatChannel
from .register import get_tool, ToolExcuteError
from . import tools

deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com")
MODEL = os.getenv("MODEL", "deepseek-chat")


class LLMChannel:

    def __init__(
        self,
        api_key: str | None = deepseek_api_key,
        base_url: str = BASE_URL,
        model: str = MODEL,
    ):

        if api_key == None:
            raise ValueError("API key can not be None")

        if base_url == None:
            raise ValueError("base_url can not be None")

        if model == None:
            raise ValueError("model name can not be None")

        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def send_request(
        self,
        messages: list,
        tools: list | None = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": self.model,
            "temperature": temperature,
            "messages": messages,
            "max_tokens": max_tokens,
        }

        if tools:
            payload["tools"] = tools

        resp = httpx.post(
            url=f"{self.base_url}/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=30,
        )
        if resp.status_code != 200:
            raise Exception(f"Request failed with status code {resp.status_code}: {resp.text}")

        return resp.json()["choices"][0]["message"]


class ReActAgent:

    def __init__(self, channel: ChatChannel, max_steps: int = 8, max_retry: int = 3):
        if max_steps < 1:
            raise ValueError("max_steps must be at least 1")

        if max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        self._max_retry = max_retry
        self._max_steps = max_steps

        self.messages: list[Any | dict[str, str]] = [{"role": "system", "content": "You are a helpful assistant."}]
        self.channel = channel
        self.trace = []

    def send_messages(
        self,
        messages: list,
        tools: list | None = None,
        temperature: float = 0.7,
        max_tokens: int = 150,
    ):
        """
        Send a request to the LLM channel and return the response.
        """
        if self._max_retry < 1:
            raise ValueError("max_retry must be at least 1")

        for attempt in range(self._max_retry):
            try:
                response = self.channel.send_request(
                    messages=messages,
                    tools=tools,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                if response is None:
                    raise ValueError("Provider returned an empty response")
                return response
            except Exception as e:
                print(f"Attempt {attempt + 1} failed: {e}")
                if attempt == self._max_retry - 1:
                    raise Exception("Attach Max retry!")
                continue

        raise AssertionError("unreachable")

    def _execute_tool(self, tool_call: dict):
        """
        Execute the tool call and return the result.
        """
        function_data = tool_call.get("function", {})
        function_name = function_data.get("name", None)
        function_args = function_data.get("arguments", None)
        trace = {
            "tool_call": tool_call,
            "function_name": function_name,
        }
        try:
            if not isinstance(function_args, str):
                raise ValueError("tool arguments must be a JSON string")
            function_args = json.loads(function_args)
            trace["function_args"] = function_args
        except (json.JSONDecodeError, ValueError) as exc:
            trace["tool_result"] = json.dumps(
                {
                    "ok": False,
                    "error": {
                        "type": "invalid_tool_arguments",
                        "message": str(exc),
                        "retryable": False,
                    },
                },
                ensure_ascii=False,
            )
            self.trace.append(trace)
            return trace["tool_result"]

        try:
            function = get_tool(fnname=function_name)
            tool_result = function.excute(**function_args)
            trace["tool_result"] = str(tool_result)
        except KeyError as e:
            trace["tool_result"] = f"Not Found the tool:{function_name}"
        except ToolExcuteError as e:
            trace["tool_result"] = f"Tool Excute Error:{e}"
        except Exception as e:
            trace["tool_result"] = f"Error:{e}"

        self.trace.append(trace)

        return trace["tool_result"]

    def chat(self, input, tools: list | None, temperature: float = 0.7, max_tokens: int = 150):
        """
        Chat with the ReAct agent using the provided messages and tools.
        """

        self.trace = []

        self.messages.append({"role": "user", "content": input})
        for step in range(self._max_steps):
            response = self.send_messages(
                messages=self.messages,
                tools=tools,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            self.messages.append(response)

            tool_calls = response.get("tool_calls")
            if not tool_calls:
                return response

            for tool_call in tool_calls:
                tool_result = self._execute_tool(tool_call)
                self.messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call["id"],
                        "content": tool_result,
                    }
                )

        raise RuntimeError(f"Agent reached max_steps={self._max_steps} before producing a final answer")
