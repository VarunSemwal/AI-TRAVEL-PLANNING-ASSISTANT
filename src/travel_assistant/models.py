from dataclasses import dataclass, field


@dataclass(frozen=True)
class Citation:
    title: str
    url: str


@dataclass
class AssistantResponse:
    answer: str
    citations: list[Citation] = field(default_factory=list)
    current_data: list[str] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)
    tools_used: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class Intent:
    needs_knowledge: bool
    needs_weather: bool
    needs_currency: bool


@dataclass(frozen=True)
class WeatherResult:
    summary: str
    daily: list[dict]
    provider: str


@dataclass(frozen=True)
class CurrencyResult:
    amount: float
    from_currency: str
    to_currency: str
    converted_amount: float
    rate: float
    date: str
    provider: str