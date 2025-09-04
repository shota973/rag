import os
import embedding
from docling.document_converter import DocumentConverter
from markitdown import MarkItDown
from langchain.text_splitter import MarkdownTextSplitter

CHUNK_SIZE = 250
markitdown_can_convert_types = (".docx", ".pptx", ".xlsx", ".xls", ".jpeg", ".jpg", ".png", ".wav", ".mp3", ".html", ".csv")

def read_docs(markitdown: MarkItDown, file_path: str) -> str:
    try:
        result = markitdown.convert(file_path)  # DocumentConverterResult
        return result.text_content or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

def read_pdf(pdf_converter: DocumentConverter, file_path: str) -> str:
    try:
        result = pdf_converter.convert(file_path)  # DocumentConverterResult
        return result.document.export_to_markdown() or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

def split_to_chunks(md_splitter: MarkdownTextSplitter, md_text: str) -> list[str]:
    if not md_text:
        return []

    docs = md_splitter.create_documents([md_text])
    docs_texts = [doc.page_content for doc in docs]
    return docs_texts

def main():  
    current_dir = os.path.join(os.getcwd(), "docs")
    markitdown = MarkItDown()
    pdf_converter = DocumentConverter()
    md_splitter = MarkdownTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=0)
    print("Files in the current directory:")
    for root, _, files in os.walk(current_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                if file.endswith(".pdf"):
                    print(f"Reading PDF file: {full_path}", flush=True)
                    md_text = read_pdf(pdf_converter, full_path)
                    # テスト用に書き出し
                    with open(full_path + ".md", 'w', encoding='utf-8') as f:
                        f.write(md_text)

                elif file.endswith(markitdown_can_convert_types):
                    print(f"Reading non-PDF file with conversion: {full_path}", flush=True)
                    md_text = read_docs(markitdown, full_path)
                    # テスト用に書き出し
                    with open(full_path + ".md", 'w', encoding='utf-8') as f:
                        f.write(md_text)

                else:
                    print(f"Reading non-PDF file without conversion: {full_path}", flush=True)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        md_text = f.read()

            except Exception as e:
                print(f"Error reading file: {full_path}: {e}", flush=True)
                continue

            contents = split_to_chunks(md_splitter, md_text)
            print(f"File: {full_path}, Number of chunks: {len(contents)}", flush=True)
            for i, chunk in enumerate(contents):
                preview = chunk[:30]
                print(f"  Chunk {i + 1}: {preview}...", flush=True)
            embedding.embedding(contents)

if __name__ == "__main__":
    main()