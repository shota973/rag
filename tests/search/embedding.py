import ollama
import model
from langchain_core.documents import Document

# 分割されたテキストの埋め込みとchroma DBへの登録
def embedding(documents: list[Document]):
    # model.pyのsetup_chroma関数からdocsコレクション、レコード数を取得
    collection, num_of_records = model.setup_chroma()
    for i, doc in enumerate(documents):
        # テキストの埋め込み処理
        response = ollama.embeddings(model=model.EMBEDDING_MODEL, prompt=doc.page_content)

        # 結果の表示
        print(response)
        print("=============")
        embeddings = response['embedding']
        print(embeddings)

        # langchainのMarkdownHeaderTextSplitterでは分割したテキストのヘッダー情報がmetadataとして格納されているため存在する場合はmetadataを登録
        if len(doc.metadata) > 0:
            collection.add(
                ids=[str(num_of_records + i)],
                embeddings=embeddings,
                documents=[doc.page_content],
                metadatas=[doc.metadata]
            )
        else:
            collection.add(
                ids=[str(num_of_records + i)],
                embeddings=embeddings,
                documents=[doc.page_content],
            )

# 埋め込み, chroma DBへの登録が正常に動作するかのテスト用
def main():
    # いけるか確認
    test_text = [Document(page_content="Today's weather in Tokyo is cloudy, with a high of 37°C. The chance of precipitation is 30%.")]
    embedding(test_text)

if __name__ == "__main__":
    main()