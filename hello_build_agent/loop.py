import json, os
from rich.console import Console
from langchain.schema import HumanMessage

from hello_build_agent.agent.tracker import tracker, TOKEN_LIMIT
from hello_build_agent.agent.logger  import emit
from hello_build_agent.agent.actions import actions, shared_context, ask_human

MAX_FAILS = int(os.getenv("QUOTA_FAILS", "3"))
console = Console()


def get_tokens_used(reply) -> int | None:
    """Return real token usage from the LLM reply, if the backend provides it."""
    try:
        if hasattr(reply, "lc_metadata") and reply.lc_metadata.get("usage"):
            return reply.lc_metadata["usage"].get("total_tokens")
        if hasattr(reply, "usage") and reply.usage:
            return reply.usage.get("total_tokens")
        if hasattr(reply, "response") and hasattr(reply.response, "usage"):
            return reply.response.usage.get("total_tokens")
    except Exception:
        pass
    return None


def event_loop(history: list, llm):
    fails = 0
    while True:
        reply = llm.invoke(history)

        # ------------------------------------------------------------------
        # 1️⃣  account tokens FIRST ─ real usage if available, else estimate
        # ------------------------------------------------------------------
        real_tokens = get_tokens_used(reply)
        if real_tokens is not None:
            tracker.add("", delta=real_tokens)      # no action/comment yet
        else:
            tracker.add(reply.content)              # estimate from text

        # ------------------------------------------------------------------
        # 2️⃣  token-quota guard
        # ------------------------------------------------------------------
        if tracker.quota_exceeded():
            emit("token-quota reached", action="ask_human",
                 params={"prompt": f"Used {tracker.tokens} tokens. Continue? [y/n]: "})
            ans = ask_human({"prompt": f"Used {tracker.tokens} tokens. Continue? [y/n]: "})
            history += [reply, HumanMessage(content=json.dumps(ans))]
            tracker.reset()
            continue

        # ------------------------------------------------------------------
        # 3️⃣  parse LLM JSON action
        # ------------------------------------------------------------------
        try:
            obj = json.loads(reply.content)
            act, prm = obj["action"], obj.get("params", {})
            cmt = obj.get("comment", "")
        except Exception:
            emit("bad json", action="error")
            console.print("[bold red]Bad JSON from LLM:[/bold red]")
            console.print(reply.content)
            break

        # Log action line with real tokens so far
        tracker.add("", action=act, comment=cmt)    # delta=None – no extra tokens

        emit(cmt, action=act, params=prm)
        result = actions.get(act, actions["unknown"])({**prm, **shared_context})

        # ------------------------------------------------------------------
        # 4️⃣  consecutive build-fail guard
        # ------------------------------------------------------------------
        if act == "build":
            if result.get("status") == "error":
                fails += 1
                if fails >= MAX_FAILS:
                    emit("too many fails", action="ask_human",
                         params={"prompt": "Build keeps failing. Continue? [y/n]: "})
                    result = ask_human({"prompt": "Build keeps failing. Continue? [y/n]: "})
                    fails = 0
            else:
                fails = 0

        history += [reply, HumanMessage(content=json.dumps(result))]

        if act == "exit":
            break
