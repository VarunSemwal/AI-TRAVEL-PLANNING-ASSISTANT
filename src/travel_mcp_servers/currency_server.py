import asyncio

from mcp.server.mcpserver import MCPServer

from travel_assistant.config import get_settings
from travel_assistant.providers import fetch_currency

server = MCPServer("singapore-currency")


@server.tool()
def convert_currency(amount: float, from_currency: str, to_currency: str) -> dict:
    """Convert an amount using current exchange-rate data."""
    result = fetch_currency(
        amount,
        from_currency,
        to_currency,
        get_settings().currency_api_url,
    )
    return {
        "amount": result.amount,
        "from_currency": result.from_currency,
        "to_currency": result.to_currency,
        "converted_amount": result.converted_amount,
        "rate": result.rate,
        "date": result.date,
        "provider": result.provider,
    }


if __name__ == "__main__":
    asyncio.run(server.run_stdio_async())