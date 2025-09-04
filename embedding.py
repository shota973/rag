import ollama
import model

def embedding(texts: list[str]):
    collection, num_of_records = model.setup_chroma()
    for i, text in enumerate(texts):
        response = ollama.embeddings(model=model.EMBEDDING_MODEL, prompt=text)

        print(response)
        print("=============")
        embeddings = response['embedding']
        print(embeddings)

        collection.add(
            ids=[str(num_of_records + i)],
            embeddings=embeddings,
            documents=[text]
        )

def main():
    test_text = ["Today's weather in Tokyo is cloudy, with a high of 37°C. The chance of precipitation is 30%."]
    embedding(test_text)

if __name__ == "__main__":
    main()