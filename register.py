from typing import Any, Callable

from pydantic import BaseModel, Field, create_model
import inspect


class ToolFnCallabelError(Exception):
    """Function can not is None"""


class ToolFnModelError(Exception):
    """Fcuntion model not valid"""


class ToolExcuteError(Exception):
    """Tool excute errir"""


class ToolFunction:

    def __init__(self, fn: Callable[..., Any] | None = None, model: type[BaseModel] | None = None):
        if fn == None:
            raise ToolFnCallabelError()
        if model == None:
            raise ToolFnModelError()
        self.fn = fn
        self.model = model

    def excute(self, **params):
        try:
            return self.fn(**params)
        except Exception as e:
            raise ToolExcuteError(e)

    def get_sechema(self):
        return {
            "type": "function",
            "function": {
                "name": self.fn.__name__,
                "description": self.fn.__doc__,
                "parameters": self.model.model_json_schema(),
            },
        }


_TOOLS: dict[str, ToolFunction] = {}


def tool(fn: Callable[..., Any]) -> Callable[..., Any]:
    """
    Decorator to  register a funtion as tool for the ReAct agent.
    Args:
        fn (callable): The function to be registered as a tool.
    Returns:
        callable: The original function, unchanged.
    """
    model = _build_params_model(fn)
    _TOOLS[fn.__name__] = ToolFunction(fn, model)
    return fn


def _build_params_model(fn: Callable[..., Any]) -> type[BaseModel]:
    """
    Build a Pydantic model for the function parameters based on the function signature.
    Args:
        fn (callable): The function to build the parameter model for.
    Returns:
        BaseModel: A Pydantic model representing the function parameters.
    """
    fileds = {}
    for p in inspect.signature(fn).parameters.values():
        default = ... if p.default is inspect.Parameter.empty else p.default
        fileds[p.name] = (p.annotation, default)
    return create_model(f"{fn.__name__}Params", **fileds)


def get_tools_schema():
    return [fn.get_sechema() for fn in _TOOLS.values()]


def get_tool(fnname) -> ToolFunction:
    return _TOOLS[fnname]
