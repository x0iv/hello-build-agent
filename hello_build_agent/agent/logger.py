from pathlib import Path
from datetime import datetime
from rich.console import Console
import json
from .tracker import tracker

ACTION_LOG = Path("/build_logs") / "actions.log"
ACTION_LOG.parent.mkdir(parents=True, exist_ok=True)
_header_printed = False
console = Console()

def append_line(path: Path, text: str):
    with open(path, "a", encoding="utf-8") as f:
        f.write(text)
        f.flush()

def emit(comment: str, *, action: str, params: dict | None = None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    short = (comment[:46] + "…") if len(comment) > 50 else comment
    tokens = tracker.tokens

    # Write one line as TSV
    append_line(
        ACTION_LOG,
        "{ts}\t{act}\t{cmt}\t{tok}\t\n".format(
            ts=ts, act=action, cmt=short, tok=tokens
        )
    )
    # Write a JSON line for easier future parsing
    append_line(
        ACTION_LOG,
        json.dumps({
            "timestamp": ts,
            "tokens": tokens,
            "comment": comment,
            "action": action,
            "params": params or {},
        }, ensure_ascii=False) + "\n"
    )
