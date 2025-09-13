import os
import sys
import embedding
from docling.document_converter import DocumentConverter
from markitdown import MarkItDown
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter
from langchain_core.documents import Document

# 1チャンク当たりの最大文字数
CHUNK_SIZE = 250
# 隣り合うチャンク同士で重なりあえる文字数
CHUNK_OVERLAP = 30
# markitdownで変換可能なファイル形式
markitdown_can_convert_types = (".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".jpeg", ".jpg", ".png", ".wav", ".mp3", ".html", ".csv")
# 分割するヘッダーの種類
headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

# doclingを使用した変換
def pdf_to_md(pdf_converter: DocumentConverter, file_path: str) -> str:
    try:
        result = pdf_converter.convert(file_path)  # DocumentConverterResult
        return result.document.export_to_markdown() or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

# markitdownを使用した変換
def docs_to_md(markitdown: MarkItDown, file_path: str) -> str:
    try:
        result = markitdown.convert(file_path)  # DocumentConverterResult
        return result.text_content or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

# markdown形式の文章の分割　markdown形式ではなかった場合、文字数のみを考えてで分割が行われる
def split_to_chunks(md_splitter: MarkdownHeaderTextSplitter, text_splitter: RecursiveCharacterTextSplitter, md_text: str) -> list[Document]:
    if not md_text:
        return []

    docs = md_splitter.split_text(md_text)
    formated_docs = text_splitter.split_documents(docs)

    return formated_docs

def main():
    # コマンドライン引数で"markitdown"が指定されたときpdfの変換にmarkitdownを使用
    args = sys.argv
    use_docling = True
    if len(args) >= 2 and args[1].lower() == "markitdown":
        use_docling = False

    # markdown変換や分割に使用するツールの作成
    markitdown = MarkItDown()
    pdf_converter = DocumentConverter()
    md_splitter = MarkdownHeaderTextSplitter(headers_to_split_on, strip_headers=False)
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP)

    # "{作業ディレクトリ}/docs"ディレクトリ以下のファイルを探索
    current_dir = os.path.join(os.getcwd(), "docs")
    print("Files in the current directory:")
    for root, _, files in os.walk(current_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                # doclingの使用が選択され、ファイルがpdf形式の時
                if use_docling and file.endswith(".pdf"):
                    print(f"Convert file with docling: {full_path}", flush=True)
                    md_text = pdf_to_md(pdf_converter, full_path)

                # markitdownで変換可能なpdf以外のファイル or markitdownをpdfで使用するときのpdf形式のファイル
                elif file.endswith(markitdown_can_convert_types):
                    print(f"Convert file with markitdown: {full_path}", flush=True)
                    md_text = docs_to_md(markitdown, full_path)

                # markdown形式に変換不可のファイル (元からmarkdown形式の場合も含む)
                else:
                    print(f"Reading file without conversion: {full_path}", flush=True)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        md_text = f.read()

            # ファイルを開くときなどにエラーが発生した場合、エラーが発生したことを出力し、ほかのファイルの変換へ移る
            except Exception as e:
                print(f"Error reading file: {full_path}: {e}", flush=True)
                continue

            # ファイルの内容を分割
            contents = split_to_chunks(md_splitter, text_splitter, md_text)
            print(f"File: {full_path}, Number of chunks: {len(contents)}", flush=True)
            # 分割結果の書き出し
            with open(r"out/" + file + r"_split.md", "w", encoding="utf-8") as f:
                for i, chunk in enumerate(contents):
                   f.write(f"\n\n===== CHUNK{i + 1} =====\n{chunk}")
            # 分割された各チャンクの一部の表示で十分な場合は以下に変更
            # for i, chunk in enumerate(contents):
            #     preview = chunk.page_content[:30]
            #     print(f"  Chunk {i + 1}: {preview}...", flush=True)

            # embedding.pyのembedding関数でchroma DBに登録
            embedding.embedding(contents)

if __name__ == "__main__":
    main()