import chromadb
# 使用するモデルを設定
EMBEDDING_MODEL = 'nomic-embed-text'
CHAT_MODEL = 'gpt-oss'
CHUNCKING_MODEL = 'gpt-oss'
CONFIG_PATH = 'mcp_setting.json'

# 指定したcollectionのレコード数を取得
def get_num_of_records(collection: chromadb.Collection) -> int:
    num_of_records = collection.count()
    return num_of_records

# chtoma DBを使うためのセットアップ
# embeddingしたデータを登録するchroma DBのdocsコレクションと既存のレコード数を返す
def setup_chroma() -> tuple[chromadb.Collection, int]:
    # chroma DBへのアクセス docker内での通信のため、コンテナ名を使ってアクセス
    chroma_client = chromadb.HttpClient(host='chromadb', port=8000)
    chroma_client.heartbeat()
    # chroma DBのcollection一覧を取得
    collections = chroma_client.list_collections()
    print(collections)
    # docsコレクションが存在する場合はそれを返答
    for collection in collections:
        print("Collection:", collection)
        if collection.name == "docs":
            return collection, get_num_of_records(collection)

    # docsコレクションが存在しない場合は作成して返答
    collection = chroma_client.create_collection(name="docs")
    num_of_records = 0
    return collection, num_of_records