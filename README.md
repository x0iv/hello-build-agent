# hello-build-agent

> **Autonomous DevOps side-kick**  
> Clones any public repo, indexes docs to Qdrant, asks an LLM to craft the
> optimal **Dockerfile**, then builds, self-repairs and logs every step.

[![PyPI](https://img.shields.io/pypi/v/hello-build-agent.svg)](https://pypi.org/project/hello-build-agent)
[![CI](https://github.com/x0iv/hello-build-agent/actions/workflows/ci-cd.yml/badge.svg?event=push)](https://github.com/x0iv/hello-build-agent/actions)
[![Docker](https://img.shields.io/docker/pulls/x0iv/hello-build-agent)](https://hub.docker.com/r/x0iv/hello-build-agent)
[![GHCR](https://img.shields.io/badge/ghcr.io%2Fx0iv%2Fhello--build--agent-blue)](https://github.com/x0iv/hello-build-agent/pkgs/container/hello-build-agent)

[Changelog](CHANGELOG.md) • [License](LICENSE)

![Demo](https://raw.githubusercontent.com/x0iv/hello-build-agent/main/peek.gif)

---

## ✨ Key features

| 🧩 | Description |
|----|-------------|
| **LLM-driven Dockerfile** | Uses OpenAI (gpt-4o-mini* by default) to propose a minimal, working Dockerfile based on real file-tree analysis. |
| **Self-healing loop**     | If the image fails to build, the agent feeds the error back to the LLM → receives a patch → retries ― until success or user input. |
| **Qdrant ingestion & search** | README and file-tree chunks are embedded and stored in Qdrant; you can query them later (`query_qdrant`). |
| **Quota guards**          | Two env-controlled limits: `QUOTA_TOKENS`, `QUOTA_FAILS` ― agent pauses and asks the human before overspending. |
| **Live Rich logs**        | Timestamp · action · comment · token-counter, neatly aligned and colourised. |
| **CI/CD ready**           | GitHub Actions → PyPI wheel + Docker Hub & GHCR images on each `vX.Y.Z` tag. |

\* Change the model with the `MODEL` env var or `--model` CLI flag.

---

## 🚀 Quick start


```bash
./quickstart.sh
```

`build_logs/` and `workspace/` are mounted on the host for inspection.

---

## 🛠️  CLI flags & env vars

| CLI flag / env                  | Default              | Purpose                                    |
| ------------------------------- | -------------------- | ------------------------------------------ |
| `--docker-host` / `DOCKER_HOST` | `tcp://dind:2375`    | Where to talk to Docker daemon             |
| `--qdrant-url` / `QDRANT_URL`   | `http://qdrant:6333` | Qdrant instance                            |
| `--model` / `MODEL`             | `gpt-4o-mini`        | OpenAI model name                          |
| `QUOTA_TOKENS`                  | `10000`              | Ask human after this many tokens           |
| `QUOTA_FAILS`                   | `3`                  | Ask human after N consecutive build errors |
| `DISABLE_HITL`                  | `false`              | `true` → fully autonomous, no prompts      |

---

## 🧭  Architecture (90 sec overview)

```
CLI ─┬─ SystemPrompt (strict JSON contract)
     │
     ├─ loop.py  (LLM ↔ actions ↔ tracker/logs)
     │     ├─ tracker  ─── prints Rich log & enforces quotas
     │     ├─ actions  ─── clone, ingest, build, …
     │     └─ logger   ─── file logs (.log) for post-mortem
     │
     └─ docker_io.py  ── minimal, tail-aware build helper
```

---


## 📜 License

This project is distributed under the **MIT License** (see `LICENSE`).

---

Made with ❤️ & LLM-powered automation.
