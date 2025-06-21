FROM python:3.12-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        git curl ca-certificates gcc gnupg && \
    rm -rf /var/lib/apt/lists/*

RUN curl -fsSL https://download.docker.com/linux/debian/gpg | \
        gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg && \
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] \
        https://download.docker.com/linux/debian $(grep VERSION_CODENAME /etc/os-release | cut -d= -f2) stable" \
        > /etc/apt/sources.list.d/docker.list && \
    apt-get update && apt-get install -y docker-ce-cli && \
    rm -rf /var/lib/apt/lists/*

LABEL org.opencontainers.image.version="$HBA_VERSION" \
    org.opencontainers.image.revision="$HBA_VERSION" \
    org.opencontainers.image.title="hello-build-agent" \
    org.opencontainers.image.description="Autonomous Dockerfile generator & build agent" \
    org.opencontainers.image.url="https://github.com/x0iv/hello-build-agent" \
    org.opencontainers.image.documentation="https://github.com/x0iv/hello-build-agent/blob/main/README.md" \
    org.opencontainers.image.source="https://github.com/x0iv/hello-build-agent" \
    org.opencontainers.image.changelog="https://github.com/x0iv/hello-build-agent/blob/main/CHANGELOG.md"


WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY hello_build_agent ./hello_build_agent
ENV PYTHONPATH=/app/hello_build_agent

CMD ["python", "-m", "hello_build_agent.cli"]
