import os
import embedding
from docling.document_converter import DocumentConverter
from markitdown import MarkItDown
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

CHUNK_SIZE = 250
CHUNK_OVERLAP = 30
markitdown_can_convert_types = (".docx", ".pptx", ".xlsx", ".xls", ".jpeg", ".jpg", ".png", ".wav", ".mp3", ".html", ".csv")
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

def docs_to_md(markitdown: MarkItDown, file_path: str) -> str:
    try:
        result = markitdown.convert(file_path)  # DocumentConverterResult
        return result.text_content or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

def pdf_to_md(pdf_converter: DocumentConverter, file_path: str) -> str:
    try:
        result = pdf_converter.convert(file_path)  # DocumentConverterResult
        return result.document.export_to_markdown() or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

def split_to_chunks(md_splitter: MarkdownHeaderTextSplitter, text_splitter: RecursiveCharacterTextSplitter, md_text: str) -> list[Document]:
    if not md_text:
        return []

    docs = md_splitter.split_text([md_text])
    formated_docs = text_splitter.split_documents(docs)

    return formated_docs

def main():  
    current_dir = os.path.join(os.getcwd(), "docs")
    markitdown = MarkItDown()
    pdf_converter = DocumentConverter()
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)
    print("Files in the current directory:")
    for root, _, files in os.walk(current_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                if file.endswith(".pdf"):
                    print(f"Reading PDF file: {full_path}", flush=True)
                    md_text = pdf_to_md(pdf_converter, full_path)
                    # テスト用に書き出し
                    with open("out/" + file + ".md", 'w', encoding='utf-8') as f:
                        f.write(md_text)

                elif file.endswith(markitdown_can_convert_types):
                    print(f"Reading non-PDF file with conversion: {full_path}", flush=True)
                    md_text = docs_to_md(markitdown, full_path)
                    # テスト用に書き出し
                    with open("out/" + file + ".md", 'w', encoding='utf-8') as f:
                        f.write(md_text)

                else:
                    print(f"Reading non-PDF file without conversion: {full_path}", flush=True)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        md_text = f.read()

            except Exception as e:
                print(f"Error reading file: {full_path}: {e}", flush=True)
                continue

            contents = split_to_chunks(md_splitter, text_splitter, md_text)
            print(f"File: {full_path}, Number of chunks: {len(contents)}", flush=True)
            for i, chunk in enumerate(contents):
                preview = chunk[:30]
                print(f"  Chunk {i + 1}: {preview}...", flush=True)
            embedding.embedding(contents)

if __name__ == "__main__":
    main()