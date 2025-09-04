import ollama
import model
import sys

def get_info(prompt: str) -> str:
    response = ollama.embed(model=model.EMBEDDING_MODEL, input=prompt)
    print(response['embeddings'], flush=True)

    collection, _ = model.setup_chroma()
    result = collection.query(query_embeddings=response['embeddings'], n_results=5)
    print(result, flush=True)
    data = result['documents'][0][0]
    return data

def generate_rag_prompt(prompt: str) -> list[dict[str, str]]:
    info = get_info(prompt)
    print("Information:", info, flush=True)
    update_prompt = [
        {"role": "user", "content": "# RAG information\n" + info},
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