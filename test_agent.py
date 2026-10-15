import json

from .schemas import TOOLS

from .main import LLMChannel, ReActAgent
from .tools import register_tools


def test_LLMchannel_init():
    agent = LLMChannel()
    response = agent.send_request([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}])
    assert response is not None


def test_errorapikey_LLMchannel_init():
    agent = LLMChannel(api_key="invalid_key")
    response = agent.send_request([{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "Hello!"}])


def test_tools():
    agent = LLMChannel()
    messages = [{"role": "system", "content": "You are a helpful assistant."}, {"role": "user", "content": "天津告诉我今天天气"}]
    response = agent.send_request(messages=messages, tools=TOOLS)
    assert response is not None
    messages.append(response)

    for tool_call in response["tool_calls"]:
        function_name = tool_call["function"]["name"]
        function_args = json.loads(tool_call["function"]["arguments"])
        tool_result = register_tools[function_name](**function_args)

        assert function_name in [tool["function"]["name"] for tool in TOOLS], f"Function {function_name} is not defined in TOOLS"
        assert function_args is not None, f"Function {function_name} was called without arguments"
        assert function_args != {}, f"Function {function_name} was called with empty arguments"
        assert function_args["city"] == "天津", f"Function {function_name} was called with incorrect city argument: {function_args['city']}"
        assert tool_result is not None, f"Function {function_name} returned None"

        messages.append({"role": "tool", "tool_call_id": tool_call["id"], "content": str(tool_result)})
        response = agent.send_request(messages=messages, tools=TOOLS)
        assert response is not None
