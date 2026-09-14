from pathlib import Path

from travel_assistant.config import get_settings
from travel_assistant.knowledge import (
    build_vector_store,
    load_documents,
    load_source_manifest,
    split_documents,
)

ROOT = Path(__file__).resolve().parents[1]


def main() -> None:
    settings = get_settings()
    source_dir = ROOT / "data" / "sources"
    records = load_source_manifest(source_dir / "sources.json")
    documents = split_documents(load_documents(source_dir, records))
    vector_store = build_vector_store(
        documents,
        endpoint=settings.azure_openai_endpoint,
        api_key=settings.azure_openai_api_key,
        api_version=settings.azure_openai_api_version,
        embedding_deployment=settings.azure_openai_embedding_deployment,
    )
    vector_store.save_local(str(ROOT / "data" / "index"))
    print(f"Indexed {len(documents)} chunks from {len(records)} sources.")


if __name__ == "__main__":
    main()