# syntax=docker/dockerfile:1
FROM --platform=$BUILDPLATFORM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337 AS build
WORKDIR /build
COPY pyproject.toml MANIFEST.in README.md SECURITY.md LICENSE THIRD_PARTY_NOTICES.md CHANGELOG.md ./
COPY src ./src
RUN python -m pip wheel --no-deps --wheel-dir /wheels .

FROM python:3.12-slim-bookworm@sha256:e697c81897302a4c4333bade000d98038fbb21eb064f8ee1fd42d02ebcd9d337
ARG VITA_CV_VERSION=2.15.0
ENV PYTHONUNBUFFERED=1 PYTHONDONTWRITEBYTECODE=1 LANG=C.UTF-8 \
    HOME=/home/vita VITA_TREE_PUBLIC_PORT=8765 VITA_TREE_LOG_DIR=/workspace/.git/vita-tree/container-logs
RUN apt-get update && apt-get install -y --no-install-recommends \
    git ca-certificates tini texlive-latex-extra texlive-fonts-recommended \
    texlive-xetex texlive-luatex texlive-science latexmk \
    fonts-dejavu-core fonts-liberation fonts-noto-core \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 1000 vita \
    && mkdir /workspace && chown vita:vita /workspace
COPY --from=build /wheels /wheels
RUN python -m pip install --no-cache-dir /wheels/*.whl "vita-cv==${VITA_CV_VERSION}" \
    && rm -rf /wheels
COPY docker/entrypoint.py /usr/local/bin/vita-container
RUN chmod 755 /usr/local/bin/vita-container
RUN apt-get update && apt-get install -y --no-install-recommends openssh-client \
    && rm -rf /var/lib/apt/lists/*
ENV VITA_CODEX=/usr/local/bin/vita-codex-client
USER vita
WORKDIR /workspace
EXPOSE 8765
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8765/health', timeout=3)"
ENTRYPOINT ["/usr/bin/tini", "--", "python", "/usr/local/bin/vita-container"]
