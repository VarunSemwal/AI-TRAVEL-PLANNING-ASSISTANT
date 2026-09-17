import re
from pathlib import Path

from langchain_core.documents import Document

from travel_assistant.config import Settings
from travel_assistant.intent import classify_request
from travel_assistant.knowledge import (
    load_documents,
    load_source_manifest,
    load_vector_store,
    retrieve_documents,
)
from travel_assistant.llm import generate_grounded_answer
from travel_assistant.mcp_client import call_local_mcp_sync
from travel_assistant.models import AssistantResponse, Citation
from travel_assistant.providers import parse_currency_question

ROOT = Path(__file__).resolve().parents[2]

# Keep knowledge-base excerpts and generated answers concise in the response.
CONTEXT_MAX_CHARS = 2000
ANSWER_MAX_CHARS = 700


def _trim(text: str, max_chars: int) -> str:
    text = text.strip()
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars].rsplit(" ", 1)[0]
    return f"{truncated}…"


class TravelAssistant:
    def __init__(self, settings: Settings):
        self.settings = settings
        source_dir = ROOT / "data" / "sources"
        records = load_source_manifest(source_dir / "sources.json")
        self.documents = load_documents(source_dir, records)
        self.vector_store = None
        index_dir = ROOT / "data" / "index"
        configured = all(
            [
                self.settings.azure_openai_endpoint,
                self.settings.azure_openai_api_key,
                self.settings.azure_openai_embedding_deployment,
            ]
        )
        if configured and (index_dir / "index.faiss").exists():
            self.vector_store = load_vector_store(
                index_dir,
                self.settings.azure_openai_endpoint,
                self.settings.azure_openai_api_key,
                self.settings.azure_openai_api_version,
                self.settings.azure_openai_embedding_deployment,
            )

    def _knowledge(self, question: str) -> tuple[str, list[Citation]]:
        if self.vector_store:
            selected = retrieve_documents(
                self.vector_store, question, self.settings.retrieval_top_k
            )
        else:
            selected = []
        terms = {term.lower() for term in question.split() if len(term) > 3}
        if not selected:
            ranked: list[tuple[int, Document]] = []
            for document in self.documents:
                score = sum(term in document.page_content.lower() for term in terms)
                ranked.append((score, document))
            selected = [
                document
                for score, document in sorted(ranked, key=lambda item: item[0], reverse=True)
                if score
            ]
        selected = selected[: self.settings.retrieval_top_k] or self.documents[:1]
        context = _trim(
            "\n\n".join(document.page_content for document in selected), CONTEXT_MAX_CHARS
        )
        citations = [
            Citation(document.metadata["source_title"], document.metadata["source_url"])
            for document in selected
        ]
        return context, citations

    def _weather(self, days: int = 3) -> dict:
        return call_local_mcp_sync(
            self.settings.weather_mcp_command,
            self.settings.weather_mcp_args,
            "get_weather",
            {"days": days},
        )

    def _currency(self, question: str) -> dict:
        parsed = parse_currency_question(question)
        if not parsed:
            raise ValueError(
                "Include an amount and currencies, for example: convert INR 50000 to SGD."
            )
        amount, from_currency, to_currency = parsed
        return call_local_mcp_sync(
            self.settings.currency_mcp_command,
            self.settings.currency_mcp_args,
            "convert_currency",
            {
                "amount": amount,
                "from_currency": from_currency,
                "to_currency": to_currency,
            },
        )

    @staticmethod
    def _is_greeting(question: str) -> bool:
        return bool(re.match(r"^\s*(hi|hello|hey|greetings|good\s+(morning|afternoon|evening|night))\b", question, re.I))

    def answer(self, question: str, history: list[dict] | None = None) -> AssistantResponse:
        if self._is_greeting(question):
            return AssistantResponse(
                answer="Hello! How can I help with your Singapore trip today?",
                citations=[],
                current_data=[],
                recommendations=[],
                limitations=[],
                tools_used=[],
            )

        intent = classify_request(question)
        citations: list[Citation] = []
        current_data: list[str] = []
        limitations: list[str] = []
        tools_used: list[str] = []
        context = ""

        if intent.needs_knowledge:
            context, citations = self._knowledge(question)

        weather = None
        if intent.needs_weather:
            try:
                weather = self._weather(3)
                tools_used.append("weather MCP")
                current_data.append(
                    f"Weather MCP ({weather['provider']}): {weather['summary']} "
                    f"Forecast: {weather['daily']}"
                )
            except Exception as error:
                limitations.append(f"Weather MCP was unavailable: {error}")

        if intent.needs_currency:
            try:
                currency = self._currency(question)
                tools_used.append("currency MCP")
                current_data.append(
                    f"Currency MCP ({currency['provider']}, {currency['date']}): "
                    f"{currency['amount']} {currency['from_currency']} = "
                    f"{currency['converted_amount']} {currency['to_currency']} "
                    f"at {currency['rate']} per unit."
                )
            except Exception as error:
                limitations.append(f"Currency MCP was unavailable: {error}")

        llm_answer = ""
        if (
            context
            and self.settings.azure_openai_endpoint
            and self.settings.azure_openai_api_key
            and self.settings.azure_openai_chat_deployment
            and self.settings.azure_openai_api_key != "replace-me"
        ):
            try:
                llm_answer = _trim(
                    generate_grounded_answer(
                        question,
                        context,
                        current_data,
                        self.settings.azure_openai_endpoint,
                        self.settings.azure_openai_api_key,
                        self.settings.azure_openai_api_version,
                        self.settings.azure_openai_chat_deployment,
                    ),
                    ANSWER_MAX_CHARS,
                )
            except Exception as error:
                limitations.append(f"Azure OpenAI response generation was unavailable: {error}")

        # Same section order and criteria for every query: only presence of data decides
        # what is shown, never the wording of the question.
        answer_parts = []
        if llm_answer:
            answer_parts.append(f"**Grounded assistant response**\n{llm_answer}")
        if current_data:
            answer_parts.append("**Current MCP information**\n" + "\n".join(current_data))
        if context:
            answer_parts.append(f"**Knowledge-base facts**\n{context}")
        if limitations:
            answer_parts.append("**Limitations**\n" + "\n".join(limitations))
        return AssistantResponse(
            answer="\n\n".join(answer_parts)
            or "The knowledge base does not contain enough information to answer that.",
            citations=citations,
            current_data=current_data,
            recommendations=[],
            limitations=limitations,
            tools_used=tools_used,
        )