from agentl import tools as _tools  # noqa: F401 - importing registers built-in tools
from agentl.register import get_tool, get_tools_schema, tool


def test_builtin_tools_are_registered():
    tool_names = {spec["function"]["name"] for spec in get_tools_schema()}

    assert {"get_weather", "get_current_time", "query_order"} <= tool_names


def test_registered_tool_executes_function():
    assert get_tool("query_order").excute(order_id="A123") == "Shipped"


def test_schema_required_fields_follow_function_signature():
    schemas = {
        spec["function"]["name"]: spec["function"]["parameters"]
        for spec in get_tools_schema()
    }

    assert schemas["get_weather"]["required"] == ["city"]
    assert schemas["query_order"]["required"] == ["order_id"]
    assert schemas["get_current_time"].get("required", []) == []
    assert schemas["get_current_time"]["properties"]["timezone"]["default"] == "Asia/Shanghai"


def test_decorator_builds_schema_from_signature():
    @tool
    def add_numbers(left: int, right: int = 1) -> int:
        """Add two integers."""
        return left + right

    registered = get_tool("add_numbers")
    parameters = registered.get_sechema()["function"]["parameters"]

    assert registered.excute(left=2, right=3) == 5
    assert parameters["properties"]["left"]["type"] == "integer"
    assert parameters["properties"]["right"]["default"] == 1
    assert parameters["required"] == ["left"]


def test_unknown_tool_is_rejected():
    try:
        get_tool("missing_tool")
    except KeyError as exc:
        assert exc.args == ("missing_tool",)
    else:
        raise AssertionError("unknown tool should raise KeyError")
