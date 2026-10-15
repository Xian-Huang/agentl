TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_current_time",
            "description": "获取指定时区的当前日期和时间。当用户问现在几点、今天几号、当前时间时使用。",
            "parameters": {
                "type": "object",
                "properties": {"timezone": {"type": "string", "description": "IANA 时区名，例如 Asia/Shanghai、America/New_York。不传默认 Asia/Shanghai"}},
                "required": [],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "查询指定城市的实时天气。当用户询问天气、温度、是否下雨、是否适合出门时使用。",
            "parameters": {"type": "object", "properties": {"city": {"type": "string", "description": "城市名，中文，例如 北京、上海、深圳"}}, "required": ["city"]},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "根据订单号查询订单状态。当用户询问订单进度、发货状态、物流信息时使用。",
            "parameters": {"type": "object", "properties": {"order_id": {"type": "string", "description": "订单号，字母数字组合，例如 A123、B456"}}, "required": ["order_id"]},
        },
    },
]
