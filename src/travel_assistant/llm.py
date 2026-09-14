from langchain_openai import AzureChatOpenAI

from travel_assistant.prompts import SYSTEM_PROMPT


def generate_grounded_answer(
    question: str,
    context: str,
    current_data: list[str],
    endpoint: str,
    api_key: str,
    api_version: str,
    deployment: str,
) -> str:
    model = AzureChatOpenAI(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=deployment,
        temperature=0,
    )
    prompt = (
        f"{SYSTEM_PROMPT}\n\n"
        f"KNOWLEDGE BASE CONTEXT:\n{context}\n\n"
        f"MCP CURRENT DATA:\n{' '.join(current_data) or 'None'}\n\n"
        f"USER QUESTION:\n{question}"
    )
    response = model.invoke(prompt)
    return str(response.content)