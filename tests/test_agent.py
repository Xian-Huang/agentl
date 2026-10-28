from copy import deepcopy
from typing import Any

from agentl.provider import ChatChannel
import pytest

from agentl import tools as _tools  # noqa: F401 - importing registers built-in tools
from agentl.main import ReActAgent
from agentl.register import get_tools_schema

TOOLS = get_tools_schema()


class FakeChannel(ChatChannel):
    def __init__(self, *responses: dict[str, Any] | Exception):
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def send_request(self, *args, **kwargs) -> dict[str, Any]:
        self.calls.append(deepcopy(kwargs))
        response = self.responses.pop(0)
        if isinstance(response, Exception):
            raise response
        return response


def test_chat_returns_final_message_without_tool_calls():
    final_message = {"role": "assistant", "content": "Hello!"}
    channel = FakeChannel(final_message)
    agent = ReActAgent(channel)

    result = agent.chat("Hi", tools=None)

    assert result == final_message
    assert len(channel.calls) == 1
    assert channel.calls[0]["tools"] is None
    assert channel.calls[0]["messages"][-1] == {"role": "user", "content": "Hi"}


def test_chat_executes_tool_and_continues_until_final_answer():
    tool_call = {
        "id": "call-weather-1",
        "type": "function",
        "function": {
            "name": "get_weather",
            "arguments": '{"city": "天津"}',
        },
    }
    tool_response = {
        "role": "assistant",
        "content": None,
        "tool_calls": [tool_call],
    }
    final_message = {"role": "assistant", "content": "天津今天天气晴朗。"}
    channel = FakeChannel(tool_response, final_message)
    agent = ReActAgent(channel)

    result = agent.chat("天津今天天气怎么样？", tools=TOOLS)

    assert result == final_message
    assert len(channel.calls) == 2
    print(agent.trace)
    assert agent.trace == [
        {
            "tool_call": tool_call,
            "function_name": "get_weather",
            "function_args": {"city": "天津"},
            "tool_result": "Today is sunny with a high of 75°F and a low of 55°F.",
        }
    ]

    tool_message = channel.calls[1]["messages"][-1]
    assert tool_message == {
        "role": "tool",
        "tool_call_id": "call-weather-1",
        "content": "Today is sunny with a high of 75°F and a low of 55°F.",
    }
    assert channel.calls[1]["tools"] == TOOLS


def test_chat_executes_every_tool_call_from_one_response():
    tool_calls = [
        {
            "id": "call-weather-1",
            "type": "function",
            "function": {"name": "get_weather", "arguments": '{"city": "上海"}'},
        },
        {
            "id": "call-order-1",
            "type": "function",
            "function": {"name": "query_order", "arguments": '{"order_id": "A123"}'},
        },
    ]
    channel = FakeChannel(
        {"role": "assistant", "content": None, "tool_calls": tool_calls},
        {"role": "assistant", "content": "完成。"},
    )
    agent = ReActAgent(channel)

    agent.chat("查询天气和订单", tools=TOOLS)

    tool_messages = channel.calls[1]["messages"][-2:]
    assert [message["tool_call_id"] for message in tool_messages] == [
        "call-weather-1",
        "call-order-1",
    ]
    assert [message["content"] for message in tool_messages] == [
        "Today is sunny with a high of 75°F and a low of 55°F.",
        "Shipped",
    ]


def test_send_messages_retries_after_channel_error():
    final_message = {"role": "assistant", "content": "Recovered"}
    channel = FakeChannel(RuntimeError("temporary failure"), final_message)
    agent = ReActAgent(channel)

    result = agent.send_messages([{"role": "user", "content": "Hi"}])

    assert result == final_message
    assert len(channel.calls) == 2


def test_trace_is_reset_for_each_chat():
    channel = FakeChannel(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-order-1",
                    "type": "function",
                    "function": {
                        "name": "query_order",
                        "arguments": '{"order_id": "B456"}',
                    },
                }
            ],
        },
        {"role": "assistant", "content": "first"},
        {"role": "assistant", "content": "second"},
    )
    agent = ReActAgent(channel=channel)
    agent.chat("first", tools=TOOLS)
    assert len(agent.trace) == 1

    agent.chat("second", tools=TOOLS)
    assert agent.trace == []


def test_chat_invalid_tool_arguments_returns_error_to_model():
    """当工具参数不是合法 JSON 时，返回错误给模型而非崩溃"""
    channel = FakeChannel(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-invalid-1",
                    "type": "function",
                    "function": {"name": "query_order", "arguments": "not-json"},
                }
            ],
        },
        {"role": "assistant", "content": "抱歉，参数格式有误。"},
    )
    agent = ReActAgent(channel=channel)

    result = agent.chat("invalid", tools=TOOLS)

    assert result == {"role": "assistant", "content": "抱歉，参数格式有误。"}
    assert len(agent.trace) == 1
    assert agent.trace[0]["function_name"] == "query_order"
    assert "error" in agent.trace[0]["tool_result"]
    assert "invalid_tool_arguments" in agent.trace[0]["tool_result"]

    tool_message = channel.calls[1]["messages"][-1]
    assert tool_message["role"] == "tool"
    assert tool_message["tool_call_id"] == "call-invalid-1"
    assert "invalid_tool_arguments" in tool_message["content"]


def test_chat_stops_after_max_steps():
    channel = FakeChannel(
        {
            "role": "assistant",
            "content": None,
            "tool_calls": [
                {
                    "id": "call-order-1",
                    "type": "function",
                    "function": {
                        "name": "query_order",
                        "arguments": '{"order_id": "A123"}',
                    },
                }
            ],
        }
    )
    agent = ReActAgent(channel=channel, max_steps=1)
    with pytest.raises(RuntimeError, match="max_steps"):
        agent.chat("loop", tools=TOOLS)

    assert len(agent.channel.calls) == 1
    assert len(agent.trace) == 1
