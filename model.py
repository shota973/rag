import chromadb
EMBEDDING_MODEL = 'nomic-embed-text'
CHAT_MODEL = 'gpt-oss'
CHUNCKING_MODEL = 'gpt-oss'
CONFIG_PATH = 'mcp_setting.json'

# 今まで登録したrecordが存在する場合は初期値の変更が必要
num_of_records = -1

def get_num_of_records(collection: chromadb.Collection) -> int:
    num_of_records = collection.count()
    return num_of_records

def setup_chroma() -> tuple[chromadb.Collection, int]:
    chroma_client = chromadb.HttpClient(host='chromadb', port=8000)
    chroma_client.heartbeat()
    collections = chroma_client.list_collections()
    print(collections)
    for collection in collections:
        print("Collection:", collection)
        if collection.name == "docs":
            return collection, get_num_of_records(collection)
        
    collection = chroma_client.create_collection(name="docs")
    num_of_records = 0
    return collection, num_of_records
