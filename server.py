from mcp.server.fastmcp import FastMCP
from typing import NamedTuple

mcp = FastMCP("My MCP Server")

@mcp.tool()
def letter_counter(word: str, letter: str) -> int:
    """
    単語の中に文字が何回現れるかを数える。

    Args:
        word: 分析する単語またはフレーズ
        letter: 出現回数を数える文字

    Returns:
        単語中にその文字が現れる回数
    """
    return word.lower().count(letter.lower())

class Task(NamedTuple):
    """
    タスクのデータ構造
    """
    name: str
    description: str
    date: str
    priority: int

@mcp.tool()
def save_tasks(tasks: list[Task]) -> list[Task]:
    """
    タスクを保存する。
    Args:
        tasks: 保存するタスクのリスト

    Returns:
        保存されたタスクのリスト
    """
    # ここでは単純に文字をリストに追加して返す
    saved_tasks = []
    for t in tasks:
        print(f"タスクを保存: {t.name}, {t.description}, {t.date}, 優先度: {t.priority}")
        saved_tasks.append(t)
    return saved_tasks

if __name__ == "__main__":
    mcp.run(transport="stdio")
