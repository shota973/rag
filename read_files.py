import os
import ast
import ollama
import re
import model
import embedding
from markitdown import MarkItDown
from langchain.text_splitter import MarkdownHeaderTextSplitter

def read_pdfs(markitdown: MarkItDown, file_path: str) -> str:
    try:
        result = markitdown.convert(file_path)  # DocumentConverterResult
        return result.text_content or ""
    except Exception as e:
        print(f"[WARN] convert失敗: {file_path}: {e}", flush=True)
        return ""

can_convert_types = (".pdf", ".docx", ".pptx", ".xlsx", ".xls", ".jpeg", ".jpg", ".png", ".wav", ".mp3", ".html", ".csv")

def split_to_chunks(md_text: str) -> list[str]:
    if not md_text:
        return []
    formated_md_text = md_text.replace("\n", "")
    prompt = [
        {"role": "system", "content": """
# Rule
## 役割
あなたは「文章分割エンジン」として振る舞い、与えられた任意の長文（小説、論文、レポートなど）を「章（Chapter）」と「節（Section）
」の階層構造に分割します。分割結果は、構造を明示したJSON形式で出力してください。

## 入力
1. 原文テキスト（改行区切り）。
2. 章・節の見出しは必ずしも統一フォーマットではなく、以下のような様式が混在していることがあります。
   - 「第1章」「第2章」
   - 「I. はじめに」「II. 背景」
   - 「1. はじめに」「1.1 背景」
   - 大文字・小文字混在、太字・下線、番号付き・番号無しなど
   - 見出し行は常に行頭にあるものとする。

## 出力
出力は以下の出力形式に従ったjson構造で行うこと。出力にjson以外の文章を含めてはいけません
### 出力形式
```json
{
  "title": "<文書全体のタイトル>",   // （任意）文書タイトルを推定できる場合のみ
  "chapters": [
    {
      "title": "<章のタイトル>",
      "sections": [
        {
          "title": "<節のタイトル>",
          "content": "<節の本文>　（改行はそのまま保持）"
        },
        ...
      ],
      "content": "<章の本文>（節に割り当てられなかった本文）"
    },
    ...
  ],
  "unclassified": "<章・節に分類できなかった本文>（任意）"
}
```
* `title` が空文字列の場合は見出しが見つからないことを示す。
* `content` は見出し行を除いた本文。本文の省略は行ってはいけません
* 章・節に属さない本文は `unclassified` に入れる。
* 入力した文章はいずれかの`title`, `content`, `unclassified`に格納し、文章の省略は行わないでください

## 分割ルール
1. **章の検出**
   - 行頭に「第[数字]章」「第[英語大文字]章」「[数字]章」「[I/II/III]章」などが現れたら章見出しとみなす。
   - 見出しの後に必ず改行が続く。
2. **節の検出**
   - 章の範囲内で、行頭に「[数字].」「[数字].[数字]」「[I/II/III].」などが現れたら節見出しとみなす。
   - 「章」の見出しに重複して同じ番号が出る場合は、最初の「章」レベルとして扱い、後続は「節」とみなす。
3. **見出しのフォーマットが不規則な場合**
   - 見出しと判定できるが番号がない場合でも、行頭が太字・大文字であるか、改行後に空白が少ない場合は見出しとみなす。
   - 見出しが複数行にわたる場合は、連続する見出し行を統合して一つのタイトルとする。
4. **階層の整合性**
   - 節の見出しが章の見出しに対して深すぎる場合は、最上位の章へ属させる。
   - 章がない状態で節が出現したら、その節はトップレベルの章（`"title": ""`）の子として扱う。
5. **本文の保持**
   - 見出し行自体は本文に含めず、タイトルとしてのみ保持する。
   - 改行や空白行はそのまま本文に保持し、可読性を保つ。

## 例
### 入力
```
第1章 はじめに
この章では、研究の背景を説明する。

1.1 背景
本研究の背景は...

1.2 目的
本研究の目的は...

第2章 方法
...
```

### 出力（本文の省略は行ってはいけません）
```json
{
  "title": "",
  "chapters": [
    {
      "title": "第1章 はじめに",
      "sections": [
        {
          "title": "1.1 背景",
          "content": "本研究の背景は..."
        },
        {
          "title": "1.2 目的",
          "content": "本研究の目的は..."
        }
      ],
      "content": "この章では、研究の背景を説明する。"
    },
    {
      "title": "第2章 方法",
      "sections": [],
      "content": "..."
    }
  ],
  "unclassified": ""
}
```
        """},
        {"role": "user", "content": "# Input text\n" + formated_md_text + """
# Rule
system promptで示したRuleに基づき# Input textで示した文章を論理的なまとまりごとに分割してください。
出力は以下の出力形式に従ったjson構造で行うこと。出力にjson以外の文章を含めてはいけません
また、本文の省略は行ってはいけません
## 出力形式
```json
{
  "title": "<文書全体のタイトル>",   // （任意）文書タイトルを推定できる場合のみ
  "chapters": [
    {
      "title": "<章のタイトル>",
      "sections": [
        {
          "title": "<節のタイトル>",
          "content": "<節の本文>　（改行はそのまま保持）"
        },
        ...
      ],
      "content": "<章の本文>（節に割り当てられなかった本文）"
    },
    ...
  ],
  "unclassified": "<章・節に分類できなかった本文>（任意）"
}
```
         """},
    ]
    print("Update Prompt:", prompt, flush=True)
    output = ollama.chat(model=model.CHUNCKING_MODEL, messages=prompt)
    print("result: ", output.message.content, flush=True)
    # list構造の抽出
    pattern = r'^\[\s*("(?:[^"\\]|\\.)*"\s*(,\s*"(?:[^"\\]|\\.)*"\s*)*)?\]$'
    repatter = re.compile(pattern)
    result = repatter.search(output.message.content).group()
    result_list = ast.literal_eval(result)
    return result_list

def main():
    current_dir = os.path.join(os.getcwd(), "docs")
    markitdown = MarkItDown()
    print("Files in the current directory:")
    for root, _, files in os.walk(current_dir):
        for file in files:
            full_path = os.path.join(root, file)
            try:
                if file.endswith(can_convert_types):
                    print(f"Reading file with conversion: {full_path}", flush=True)
                    md_text = read_pdfs(markitdown, full_path)
                    with open(full_path + ".md", 'w', encoding='utf-8') as f:
                        f.write(md_text)
                    content = split_to_chunks(md_text)
                else:
                    print(f"Reading file without conversion: {full_path}", flush=True)
                    with open(full_path, 'r', encoding='utf-8') as f:
                        text_content = f.read()
                    content = split_to_chunks(text_content)
            except Exception as e:
                print(f"Error reading file: {full_path}: {e}", flush=True)
                continue

            print(f"File: {full_path}, Number of chunks: {len(content)}", flush=True)
            for i, chunk in enumerate(content):
                preview = chunk.replace("\n", " ")[:30]
                print(f"  Chunk {i + 1}: {preview}...", flush=True)
            embedding.embedding(content)

if __name__ == "__main__":
    main()