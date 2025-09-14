# node:24.7-trixie-slimというimageをもとにimageを構築
# 以下で作成されるimageにuv_initという名前を付ける
FROM node:24.7-trixie-slim AS uv_init

# 以下のコマンドなどの実行を/appディレクトリで行う
WORKDIR /app

# uvのインストールのためにcurlをインストール ファイル操作できるようにvimをインストール
RUN apt-get update && apt-get install -y \
    curl \
    vim \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# uvのインストール(現状の最新版の0.8.15を指定)
RUN curl -LsSf https://astral.sh/uv/0.8.15/install.sh | sh
# uv, uvxのパスを通す 日本語を表示できるようにLANGを設定
ENV PATH="/root/.local/bin:$PATH" \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_LINK_MODE=copy \
    LANG=C.utf8

# ローカルの作業ディレクトリ内のファイルををコピー
COPY . .


# node:24.7-trixie-slimというimageをもとにimageを構築
# 以下で作成されるimageにuv_syncという名前を付ける
FROM node:24.7-trixie-slim AS uv_sync

# 以下のコマンドなどの実行を/appディレクトリで行う
WORKDIR /app

# uvのインストールのためにcurlをインストール ファイル操作できるようにvimをインストール
RUN apt-get update && apt-get install -y \
    curl \
    vim \
 && apt-get clean \
 && rm -rf /var/lib/apt/lists/*

# uvのインストール(現状の最新版の0.8.15を指定)
RUN curl -LsSf https://astral.sh/uv/0.8.15/install.sh | sh
# uv, uvxのパスを通す 日本語を表示できるようにLANGを設定
ENV PATH="/root/.local/bin:$PATH" \
    UV_CACHE_DIR=/root/.cache/uv \
    UV_LINK_MODE=copy \
    LANG=C.utf8

# 依存解決用ファイルのみを先にコピー
COPY pyproject.toml uv.lock* ./
# 仮想環境を構築（cacheを保存）
RUN --mount=type=cache,target=/root/.cache/uv \
    (uv sync --frozen || uv sync)

# ローカルの作業ディレクトリ内のファイルををコピー
COPY . .

CMD ["uv", "run", "hello.py"]