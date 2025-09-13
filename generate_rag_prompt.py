import ollama
import sys
import model
import chroma_util

# chroma DBからpromptを用いた検索により関連情報を取得し、RAGのプロンプトを生成する
def get_info(prompt: str) -> list[str]:
    # promptを埋め込みベクトルで表現
    response = ollama.embed(model=model.EMBEDDING_MODEL, input=prompt)
    print(response['embeddings'], flush=True)

    # promptの埋め込みベクトルを用いてChroma DBから関連情報を取得
    collection, _ = chroma_util.setup_chroma()
    result = collection.query(query_embeddings=response['embeddings'], n_results=4)
    print(result, flush=True)

    # 取得した関連情報のメタデータを用いて、さらに類似情報をChroma DBから取得
    docs: list[str] = []
    for i, meta in enumerate(result['metadatas'][0]):

        # metadataが複数ある場合はAND条件で検索
        if len(meta) > 2:
            similar_docs = collection.query(query_embeddings=response['embeddings'], n_results=4, where={
                "$and": [meta]
            })
        # metadataが1つだけの場合はその条件で検索
        elif len(meta) == 1:
            similar_docs = collection.query(query_embeddings=response['embeddings'], n_results=4, where=meta)
        # metadataが空の場合は取得したドキュメントの埋め込みベクトルで検索
        else:
            doc_embedding = result['embeddings'][0][i]
            similar_docs = collection.query(query_embeddings=doc_embedding, n_results=4)
            continue

        # 取得した類似ドキュメントを表示、リストに追加して返答
        print(f"Similar docs for metadata {i+1}:", similar_docs, flush=True)
        for doc in similar_docs['documents'][0]:
            if doc not in docs:
                docs.append(doc)

    return docs

# RAGによる情報を加えたのプロンプトを生成
def generate_rag_prompt(prompt: str) -> list[dict[str, str]]:
    info = get_info(prompt)
    update_prompt = [
        {"role": "system", "content": "ユーザーから与えられる'# RAG Information'を参考にして'# question'に答えてください。"},
        {"role": "user", "content": "# RAG information\n" + "\n\n".join(info)},
        {"role": "user", "content": "# question\n" + prompt}
    ]
    print("Update Prompt:", update_prompt, flush=True)
    return update_prompt

# rag単体での動作確認用
def main():
    # コマンドライン引数からプロンプトを取得
    prompt = "こんにちは"
    args = sys.argv
    if len(args) >= 2:
        prompt = " ".join(args[1:])
        
    # RAGのプロンプトを生成してチャットモデルに渡す
    update_prompt = generate_rag_prompt(prompt)
    answer = ollama.chat(model=model.CHAT_MODEL, messages=update_prompt)
    print("Answer:", answer, flush=True)

if __name__ == "__main__":
    main()