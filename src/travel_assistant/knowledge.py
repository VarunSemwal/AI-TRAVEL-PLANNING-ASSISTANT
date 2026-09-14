import json
from dataclasses import dataclass
from pathlib import Path

from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from langchain_openai import AzureOpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter


@dataclass(frozen=True)
class SourceRecord:
    title: str
    url: str
    path: str
    license_notes: str


def load_source_manifest(manifest_path: Path) -> list[SourceRecord]:
    records = json.loads(manifest_path.read_text(encoding="utf-8"))
    return [SourceRecord(**record) for record in records]


def load_documents(source_dir: Path, records: list[SourceRecord]) -> list[Document]:
    documents = []
    for source in records:
        document_path = source_dir / source.path
        if not document_path.exists():
            raise FileNotFoundError(
                f"Missing source document '{document_path}'. Add it or update sources.json."
            )
        documents.append(
            Document(
                page_content=document_path.read_text(encoding="utf-8"),
                metadata={
                    "source_title": source.title,
                    "source_url": source.url,
                    "source_path": source.path,
                    "license_notes": source.license_notes,
                },
            )
        )
    return documents


def split_documents(documents: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=900,
        chunk_overlap=150,
        separators=["\n## ", "\n# ", "\n\n", "\n", ". ", " "],
    )
    return splitter.split_documents(documents)


def build_vector_store(
    documents: list[Document],
    endpoint: str,
    api_key: str,
    api_version: str,
    embedding_deployment: str,
) -> FAISS:
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=embedding_deployment,
    )
    return FAISS.from_documents(documents, embeddings)


def retrieve_documents(vector_store: FAISS, question: str, top_k: int = 5) -> list[Document]:
    return vector_store.similarity_search(question, k=top_k)


def load_vector_store(
    index_dir: Path,
    endpoint: str,
    api_key: str,
    api_version: str,
    embedding_deployment: str,
) -> FAISS:
    embeddings = AzureOpenAIEmbeddings(
        azure_endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        azure_deployment=embedding_deployment,
    )
    return FAISS.load_local(
        str(index_dir), embeddings, allow_dangerous_deserialization=True
    )