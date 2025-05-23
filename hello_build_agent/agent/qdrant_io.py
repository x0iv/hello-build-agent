from pathlib import Path
from qdrant_client import QdrantClient, models as qdrant_models
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.docstore.document import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from .tracker import tracker

_splitter = RecursiveCharacterTextSplitter(chunk_size=400, chunk_overlap=40)

def _ensure(cli: QdrantClient, name: str, size: int) -> None:
    if name not in [c.name for c in cli.get_collections().collections]:
        cli.create_collection(
            name,
            vectors_config=qdrant_models.VectorParams(size=size, distance=qdrant_models.Distance.COSINE)
        )

def ingest(text: str, qdrant_url: str, collection: str) -> str:
    pieces = _splitter.split_text(text)
    docs   = [Document(page_content=p) for p in pieces]
    emb    = OpenAIEmbeddings()
    cli    = QdrantClient(url=qdrant_url, timeout=30)
    _ensure(cli, collection, len(emb.embed_query("ping")))
    Qdrant.from_documents(docs, emb, url=qdrant_url, collection_name=collection)
    tracker.add(" ".join(pieces))
    return f"{len(pieces)} chunks"
