import re
from datetime import date, timedelta

import httpx

from travel_assistant.models import CurrencyResult, WeatherResult


def fetch_weather(latitude: float, longitude: float, timezone: str, days: int = 3) -> WeatherResult:
    response = httpx.get(
        "https://api.open-meteo.com/v1/forecast",
        params={
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,precipitation,rain,weather_code",
            "daily": "weather_code,temperature_2m_max,precipitation_probability_max",
            "forecast_days": min(max(days, 1), 16),
            "timezone": timezone,
        },
        timeout=15,
    )
    response.raise_for_status()
    payload = response.json()
    daily = [
        {
            "date": day,
            "weather_code": code,
            "high_c": high,
            "rain_probability": rain,
        }
        for day, code, high, rain in zip(
            payload["daily"]["time"],
            payload["daily"]["weather_code"],
            payload["daily"]["temperature_2m_max"],
            payload["daily"]["precipitation_probability_max"],
        )
    ]
    current = payload.get("current", {})
    return WeatherResult(
        summary=(
            f"{current.get('temperature_2m', 'unknown')} C currently; "
            f"precipitation {current.get('precipitation', 'unknown')} mm."
        ),
        daily=daily,
        provider="Open-Meteo",
    )


def fetch_currency(
    amount: float, from_currency: str, to_currency: str, base_url: str
) -> CurrencyResult:
    from_currency = from_currency.upper()
    to_currency = to_currency.upper()
    response = httpx.get(
        f"{base_url.rstrip('/')}/latest",
        params={"amount": amount, "from": from_currency, "to": to_currency},
        timeout=15,
        follow_redirects=True,
    )
    response.raise_for_status()
    try:
        payload = response.json()
    except ValueError as error:
        raise RuntimeError("Currency provider returned a non-JSON response") from error
    converted = float(payload["rates"][to_currency])
    return CurrencyResult(
        amount=amount,
        from_currency=from_currency,
        to_currency=to_currency,
        converted_amount=converted,
        rate=converted / amount,
        date=payload.get("date", date.today().isoformat()),
        provider="Frankfurter",
    )


def parse_currency_question(question: str) -> tuple[float, str, str] | None:
    match = re.search(
        r"(?:\b([A-Z]{3})\s*)?\b([\d,]+(?:\.\d+)?)(?:\s*([A-Z]{3})\b)?",
        question,
        re.I,
    )
    if not match:
        return None
    target = re.search(r"\b(?:to|in)\s+([A-Z]{3})\b", question, re.I)
    source = re.search(r"\bfrom\s+([A-Z]{3})\b", question, re.I)
    amount = float(match.group(2).replace(",", ""))
    from_currency = (
        match.group(1) or match.group(3) or (source.group(1) if source else "INR")
    ).upper()
    to_currency = target.group(1).upper() if target else "SGD"
    return amount, from_currency, to_currency


def next_week_dates() -> list[str]:
    start = date.today() + timedelta(days=(7 - date.today().weekday()))
    return [(start + timedelta(days=index)).isoformat() for index in range(3)]