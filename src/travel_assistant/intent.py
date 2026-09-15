import re

from travel_assistant.models import Intent

WEATHER_TERMS = re.compile(r"weather|forecast|rain|temperature|sunny|umbrella", re.I)
CURRENCY_TERMS = re.compile(r"currency|convert|exchange rate|budget|\bINR\b|\bSGD\b|\bUSD\b", re.I)
GREETING_TERMS = re.compile(
    r"^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|night))\b",
    re.I,
)
TRAVEL_TERMS = re.compile(
    r"singapore|attraction|neighbourhood|neighborhood|transport|food|itinerary|museum|garden|visit|activity",
    re.I,
)


def classify_request(question: str) -> Intent:
    normalized = question.strip()
    if GREETING_TERMS.match(normalized):
        return Intent(needs_knowledge=False, needs_weather=False, needs_currency=False)

    return Intent(
        needs_knowledge=bool(TRAVEL_TERMS.search(question)) or not bool(
            WEATHER_TERMS.search(question) or CURRENCY_TERMS.search(question)
        ),
        needs_weather=bool(WEATHER_TERMS.search(question)),
        needs_currency=bool(CURRENCY_TERMS.search(question)),
    )