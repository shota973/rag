import ollama
import model
import sys

def get_info(prompt: str) -> list[str]:
    response = ollama.embed(model=model.EMBEDDING_MODEL, input=prompt)
    print(response['embeddings'], flush=True)

    collection, _ = model.setup_chroma()
    result = collection.query(query_embeddings=response['embeddings'], n_results=4)
    print(result, flush=True)

    docs: list[str] = []
    for i, meta in enumerate(result['metadatas'][0]):
        if len(meta) > 2:
            similar_docs = collection.query(query_embeddings=response['embeddings'], n_results=4, where={
                "$and": [meta]
            })
        elif len(meta) == 1:
            similar_docs = collection.query(query_embeddings=response['embeddings'], n_results=4, where=meta)
        else:
            docs.append(result['metadatas'][0][i])
            continue
        
        print(f"Similar docs for metadata {i+1}:", similar_docs, flush=True)
        for doc in similar_docs['documents'][0]:
            if doc not in docs:
                docs.append(doc)

    return docs

def generate_rag_prompt(prompt: str) -> list[dict[str, str]]:
    info = get_info(prompt)
    update_prompt = [
        {"role": "user", "content": "# RAG information\n" + "\n\n".join(info)},
        {"role": "user", "content": "# question\n" + prompt}
    ]
    print("Update Prompt:", update_prompt, flush=True)
    return update_prompt

def main():
    prompt = "こんにちは"
    args = sys.argv
    if len(args) >= 2:
        prompt = " ".join(args[1:])
        
    update_prompt = generate_rag_prompt(prompt)
    answer = ollama.chat(model=model.CHAT_MODEL, messages=update_prompt)
    print("Answer:", answer, flush=True)

if __name__ == "__main__":
    main()