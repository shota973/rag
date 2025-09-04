ollamaのembedding modelを使ってベクトル化
docker上のchromadbに保存
RAGとして利用


# spacy
日本語、英語のモデルを別途ダウンロードするためにpipが必要なため`uv add spacy`とは別に
`uv add pip`した後`uv run -- spacy download 'ja_core_news_sm'`, `uv run -- spacy download 'en_core_web_sm'`をする
（uv lockに書かれてそう）
smはsmallサイズのモデルのためmd, lgを使うと大きくなる