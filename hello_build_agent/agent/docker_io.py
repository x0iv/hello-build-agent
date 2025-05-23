# hello_build_agent/agent/docker_io.py
import json
import tempfile
import textwrap
from collections import deque
from pathlib import Path

import docker
from docker.errors import BuildError

DEFAULT_DF = textwrap.dedent(
    """\
    FROM alpine:latest
    CMD ["echo","hello"]
    """
)


def _to_str(chunk: bytes | str) -> str:
    """Convert raw byte line from Docker API to plain text."""
    if isinstance(chunk, (bytes, bytearray)):
        try:
            return chunk.decode("utf-8", "replace")
        except Exception:
            return str(chunk)
    return str(chunk)


def build(host: str, dockerfile: str, tag: str = "built") -> dict:
    """
    Build an image and return either
      {"status":"ok",    "log_tail": "<last-400-chars>"}
      {"status":"error", "error":    "<last-400-chars>"}
    """
    client = docker.DockerClient(base_url=host)

    with tempfile.TemporaryDirectory() as tmp:
        Path(tmp, "Dockerfile").write_text(dockerfile)

        try:
            # decode=False  →  raw bytes, each line is JSON string
            _, stream = client.images.build(path=tmp, tag=tag, rm=True, decode=False)
            tail = deque(maxlen=40)  # ~40 lines  → ~400 chars

            for raw in stream:
                # each `raw` is a JSON line (bytes)
                try:
                    obj = json.loads(_to_str(raw))
                    txt = obj.get("stream") or obj.get("error") or ""
                except Exception:
                    txt = _to_str(raw)
                tail.append(txt)

            return {"status": "ok", "log_tail": "".join(tail)[-400:]}

        except BuildError as e:
            # e.build_log is a generator of bytes → parse same way
            tail = deque(maxlen=40)
            for raw in getattr(e, "build_log", []):
                try:
                    obj = json.loads(_to_str(raw))
                    txt = obj.get("stream") or obj.get("error") or ""
                except Exception:
                    txt = _to_str(raw)
                tail.append(txt)

            err_tail = "".join(tail)[-400:]
            return {"status": "error", "error": err_tail}
