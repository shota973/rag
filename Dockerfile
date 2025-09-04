FROM ghcr.io/astral-sh/uv:python3.12-bookworm-slim

WORKDIR /app

# uv 設定: プロジェクト用永続環境を /opt/venv に固定
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# 依存解決用ファイルのみを先にコピーしてキャッシュ層を最大化
COPY pyproject.toml uv.lock* ./

# 依存を同期して永続仮想環境を構築（lock が壊れている / 差分がある場合はフォールバック）
RUN --mount=type=cache,target=/root/.cache/uv \
    (uv sync --frozen || uv sync)

# アプリ本体を後からコピー
COPY . .

# npm / npxのインストール (npxを必要とするmcpを使用する場合 docker compose up に時間を要するため注意)
# RUN apt-get update -qq && apt-get install -y nodejs npm

# 実行時は既存の永続環境をそのまま利用し、ephemeral 環境を作らない
CMD ["python", "hello.py"]