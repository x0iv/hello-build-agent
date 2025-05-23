"""
Tracks real token usage and prints a rich, single-line log:
timestamp | action | comment | tokens

`add()` can be called in two ways:
1. add(txt, action, comment)          -> estimates tokens from txt
2. add("", action, comment, delta=N)  -> add given token count (from usage)
"""

import os
from pathlib import Path
from time import time
from datetime import datetime

from rich.console import Console

TOKEN_LIMIT = int(os.getenv("QUOTA_TOKENS", "10000"))
LOG_PATH    = Path("/build_logs") / "usage.log"
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)


class Tracker:
    def __init__(self) -> None:
        self.tokens = 0
        self.start  = time()
        self.console = Console()

    # --------------------------------------------------------------
    # delta : int | None     – add exactly N tokens (preferred)
    # txt   : str            – fallback, estimate tokens = len(txt)//4
    # --------------------------------------------------------------
    def add(self, txt: str = "", *, action: str = "", comment: str = "",
            delta: int | None = None) -> None:
        if delta is not None:
            self.tokens += delta
        else:
            self.tokens += max(1, len(txt) // 4)

        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        short = (comment[:46] + "…") if len(comment) > 50 else comment

        if not action:
            return
        self.console.print(
            f"[cyan]{ts}[/] [yellow]{action:<24}[/] "
            f"[white]{short:<50}[/] [green]{self.tokens:>6} tok"
        )

    def reset(self) -> None:
        self.tokens = 0

    def quota_exceeded(self) -> bool:
        return self.tokens > TOKEN_LIMIT

    def dump(self) -> None:
        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(f"{int(time() - self.start)}s | tok={self.tokens}\n")


tracker = Tracker()
