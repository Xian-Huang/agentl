def get_weather(city: str):
    """Get the current weather information."""
    return "Today is sunny with a high of 75°F and a low of 55°F."


def get_current_time(timezone: str = "Asia/Shanghai"):
    """Get the current date and time in the specified timezone."""
    from datetime import datetime
    import pytz
    tz = pytz.timezone(timezone)
    now = datetime.now(tz)
    return now.strftime("%Y-%m-%d %H:%M:%S")


def query_order(order_id: str):
    """Query the order status based on the order ID."""
    # Simulate order status retrieval
    order_status = {
        "A123": "Shipped",
        "B456": "Processing",
        "C789": "Delivered"
    }
    return order_status.get(order_id, "Order ID not found.")



register_tools = {
    "get_weather": get_weather,
    "get_current_time": get_current_time,
    "query_order": query_order
}