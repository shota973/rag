import ollama
import model
from langchain_core.documents import Document

def embedding(documents: list[Document]):
    collection, num_of_records = model.setup_chroma()
    for i, doc in enumerate(documents):
        response = ollama.embeddings(model=model.EMBEDDING_MODEL, prompt=doc.page_content)

        print(response)
        print("=============")
        embeddings = response['embedding']
        print(embeddings)

        collection.add(
            ids=[str(num_of_records + i)],
            embeddings=embeddings,
            documents=[doc.page_content],
            metadatas=[doc.metadata]
        )

def main():
    test_text = ["Today's weather in Tokyo is cloudy, with a high of 37°C. The chance of precipitation is 30%."]
    embedding(test_text)

if __name__ == "__main__":
    main()