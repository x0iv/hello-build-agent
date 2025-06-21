# Changelog


All notable changes to this project are documented in this file. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## Unreleased

## v0.5.6 - 2025-06-21

### Added

* Docker image published to GitHub Container Registry (ghcr.io) alongside Docker Hub.

## v0.5.5 - 2025‑05‑25

### Added

* **`DISABLE_HITL`** environment variable to run the agent fully autonomously (no human‑in‑the‑loop prompts).
* **`write_report`** action that creates `/workspace/REPORT.md` containing the final Dockerfile and usage instructions.
* Automatic lookup of the most recent Dockerfile when `write_report` is called without the `dockerfile` parameter.
* Placeholder animated demo GIF (`peek.gif`) linked at the top of the README.

### Changed

* **`ask_human`** now prints a conspicuous banner prompt and respects `DISABLE_HITL`.
* All code comments switched to English for consistency.
* System prompt expanded to list `write_report`, new env flag, and updated workflow description.

---

## v0.5.0 - 2025‑05-23

### Added

* Initial public release: autonomous repo ingestion, LLM‑generated Dockerfile, self‑healing build loop, Qdrant integration, Rich logs, GitHub Actions CI/CD.
