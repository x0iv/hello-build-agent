import os
import typer
from dotenv import load_dotenv
from rich.console import Console
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage

from hello_build_agent.loop import event_loop
from hello_build_agent.agent.actions import shared_context

app = typer.Typer()
console = Console()

@app.command()
def run(
    repo_url: str,
    docker_host: str = os.getenv("DOCKER_HOST", "tcp://dind:2375"),
    qdrant_url: str = os.getenv("QDRANT_URL", "http://qdrant:6333"),
    model: str = os.getenv("MODEL", "gpt-4o-mini")
):
    load_dotenv()
    if "OPENAI_API_KEY" not in os.environ:
        console.print("[red]OPENAI_API_KEY missing")
        raise typer.Exit(1)

    quota_fails = int(os.getenv("QUOTA_FAILS", "3"))
    quota_tokens = int(os.getenv("QUOTA_TOKENS", "10000"))

    llm = ChatOpenAI(model=model, temperature=0.2)

    shared_context.update(
        dict(docker_host=docker_host, qdrant_url=qdrant_url, llm=llm)
    )

    system = SystemMessage(f"""You are an **expert DevOps engineer**.  
Before proposing a Dockerfile you MUST:

1. Inspect the file list and decide *what kind of project it is*
2. Verify that all commands in the Dockerfile will succeed
3. If nothing can be built, propose a minimal Dockerfile that serves static docs or prints a helpful message instead.
You are also a build-agent controller.
Respond ONLY with a single-line JSON object:

  {{"action":"<string>","params":{{...}},"comment":"<short human comment>"}}

Example (exactly one line):
  {{"action":"clone_repo","params":{{"url":"https://github.com/example/repo"}},"comment":"Cloning repo"}}

Never add extra fields, never use markdown or line-breaks.

Flow:
  clone_repo → ingest_filetree → (ingest_file?) → query_qdrant* →
  generate_dockerfile → build.
  On build failure → fix_dockerfile(dockerfile,error) → build.
  If {quota_fails} consecutive build errors OR {quota_tokens} tokens are
  consumed → ask_human.
  Finish with exit.

Allowed actions & required params:
  clone_repo          {{url}}
  ingest_file         {{file}}
  ingest_filetree     {{repo_path}}
  generate_dockerfile {{repo_path}}
  build               {{dockerfile,tag?}}
  fix_dockerfile      {{dockerfile,error}}
  query_qdrant        {{query}}
  ask_human           {{prompt}}
  exit""")

    event_loop([system, HumanMessage(content=repo_url)], llm)

if __name__ == "__main__":
    app()
