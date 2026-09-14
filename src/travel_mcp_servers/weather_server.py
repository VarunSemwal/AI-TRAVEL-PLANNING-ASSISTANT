import asyncio

from mcp.server.mcpserver import MCPServer

from travel_assistant.config import get_settings
from travel_assistant.providers import fetch_weather

server = MCPServer("singapore-weather")


@server.tool()
def get_weather(days: int = 3) -> dict:
    """Return the current Singapore weather and a forecast."""
    settings = get_settings()
    result = fetch_weather(
        settings.singapore_latitude,
        settings.singapore_longitude,
        settings.singapore_timezone,
        days,
    )
    return {"summary": result.summary, "daily": result.daily, "provider": result.provider}


if __name__ == "__main__":
    asyncio.run(server.run_stdio_async())