"""
hello_build_agent/agent/actions.py
----------------------------------
All executable actions the LLM can invoke.

• Use the @reg decorator to add a new action.
• `shared_context` is filled by cli.py and injected into every call.
"""

from pathlib import Path
from typing import Dict, Any, Callable
import shutil
import os

from git import Repo
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from qdrant_client import QdrantClient, models as qdrant_models

from .logger import emit
from .tracker import tracker
from . import docker_io, qdrant_io

# ----------------------------------------------------------------------
# shared context (docker_host, qdrant_url, llm) is populated in cli.py
# ----------------------------------------------------------------------
shared_context: Dict[str, Any] = {}

Action = Callable[[Dict[str, Any]], Dict[str, Any]]
actions: Dict[str, Action] = {}


def reg(name: str):
    """Decorator: register a function in the `actions` dict."""
    def wrap(fn: Action):
        actions[name] = fn
        return fn
    return wrap


# ─────────────────────────── simple helpers ────────────────────────────
@reg("clone_repo")
def clone_repo(p: dict):
    """params: {url}"""
    dest = Path("/workspace") / p["url"].split("/")[-1]
    if dest.exists():
        shutil.rmtree(dest)
    Repo.clone_from(p["url"], dest, depth=1, no_single_branch=True)
    return {"status": "ok", "repo_path": str(dest)}


@reg("ingest_filetree")
def ingest_tree(p: dict):
    """params: {repo_path, qdrant_url}"""
    rp = Path(p["repo_path"])
    listing = "\n".join(str(f.relative_to(rp)) for f in rp.rglob("*") if f.is_file())
    res = qdrant_io.ingest(listing, p["qdrant_url"], "hello-build-agent")
    return {"status": "ok", "result": res}


@reg("ingest_file")
def ingest_file(p: dict):
    """params: {file, qdrant_url}"""
    path = Path(p["file"])
    if not path.exists():
        return {"status": "error", "error": "file not found"}
    res = qdrant_io.ingest(
        path.read_text(encoding="utf-8", errors="ignore"),
        p["qdrant_url"],
        "hello-build-agent",
    )
    return {"status": "ok", "result": res}


@reg("query_qdrant")
def query_qdrant(p: dict):
    """params: {query, qdrant_url}"""
    emb = OpenAIEmbeddings()
    vec = emb.embed_query(p["query"])

    cli = QdrantClient(url=p["qdrant_url"], timeout=30)

    # New API – pass the vector directly
    hits = cli.search(
        collection_name="hello-build-agent",
        query_vector=vec,
        limit=5,
        with_payload=True,
    )

    return {
        "status": "ok",
        "hits": [
            {
                "score": h.score,
                "text": (h.payload.get("page_content") or "")[:120],
            }
            for h in hits
        ],
    }



# ─────────────────────── Dockerfile generation ────────────────────────
def _llm_generate_dockerfile(repo_path: Path, llm: ChatOpenAI) -> str:
    """Ask the same LLM to create a minimal Dockerfile for the project."""
    file_list = "\n".join(
        str(p.relative_to(repo_path)) for p in repo_path.rglob("*") if p.is_file()
    )[:8000]  # truncate to keep prompt short
    sys = SystemMessage(
        "You are an expert DevOps engineer. "
        "Given a list of project files, output ONLY the Dockerfile content."
    )
    usr = HumanMessage(f"Project files:\n{file_list}\n\nGenerate Dockerfile:")
    reply = llm.invoke([sys, usr])
    return reply.content.strip()


@reg("generate_dockerfile")
def generate_dockerfile(p: dict):
    """
    Two modes:
    1. LLM already provided 'dockerfile' → return it.
    2. Only 'repo_path' given → call helper to generate it via LLM.
    """
    if "dockerfile" in p:
        return {"status": "ok", "dockerfile": p["dockerfile"]}

    repo_path = p.get("repo_path")
    llm = p.get("llm")
    if not repo_path or llm is None:
        return {"status": "error", "error": "need 'dockerfile' or ('repo_path' + 'llm')"}

    try:
        df = _llm_generate_dockerfile(Path(repo_path), llm)
        return {"status": "ok", "dockerfile": df}
    except Exception as e:
        return {"status": "error", "error": str(e)}


# ────────────────────────── Docker build / fix ─────────────────────────
@reg("build")
def build_image(p: dict):
    """params: {dockerfile, docker_host}"""
    return docker_io.build(p["docker_host"], p["dockerfile"])


@reg("fix_dockerfile")
def fix_dockerfile(p: dict):
    """params: {dockerfile, error}"""
    return {
        "status": "patched",
        "dockerfile": p.get("dockerfile", ""),
        "error": p.get("error", ""),
    }


# ───────────────────────────── misc actions ────────────────────────────
@reg("ask_human")
def ask_human(p: dict):
    """params: {prompt}"""
    ans = input(f"\n[LLM] {p.get('prompt', 'Continue? [y/n]: ')} ").strip().lower()[:1] or "n"
    return {"status": "ok", "answer": ans}


@reg("exit")
def exit_app(_: dict):
    tracker.dump()
    raise SystemExit


# fallback – avoids KeyError in loop.py
@reg("unknown")
def unknown_action(p: dict):
    return {"status": "error", "error": f"unknown action {p}"}
