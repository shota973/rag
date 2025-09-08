FROM node:24.7-trixie-slim AS uv_init

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

#uvのインストール(現状の最新版の0.8.15を指定)
RUN curl -LsSf https://astral.sh/uv/0.8.15/install.sh | sh
# uv, uvxのパスを通す
ENV PATH="/root/.local/bin:$PATH" \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_LINK_MODE=copy

# アプリ本体を後からコピー
COPY . .

# 実行時は既存の永続環境をそのまま利用し、ephemeral 環境を作らない
CMD ["uv", "run", "hello.py"]

FROM node:24.7-trixie-slim AS uv_sync

WORKDIR /app

RUN apt-get update && apt-get install -y \
    curl \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

#uvのインストール(現状の最新版の0.8.15を指定)
RUN curl -LsSf https://astral.sh/uv/0.8.15/install.sh | sh
# uv, uvxのパスを通す
ENV PATH="/root/.local/bin:$PATH" \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_LINK_MODE=copy

# 依存解決用ファイルのみを先にコピー
COPY pyproject.toml uv.lock* ./
# 依存を同期して仮想環境を構築（cacheを保存）
RUN --mount=type=cache,target=/root/.cache/uv \
    (uv sync --frozen || uv sync)

# アプリ本体を後からコピー
COPY . .

# 実行時は既存の永続環境をそのまま利用し、ephemeral 環境を作らない
CMD ["uv", "run", "hello.py"]