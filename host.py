import os
import sys
import json
import asyncio
import model
import generate_rag_prompt

from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

# mcp_setting.jsonの内容を取得
def load_json_config(path=model.CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# mcp clientやReAct agentの作成
async def create_client(mcp_setting_config):
    llm = ChatOllama(
        model = model.CHAT_MODEL,
        temperature = 0,
        base_url = "http://ollama:11434"
    )
    client = MultiServerMCPClient(mcp_setting_config)
    tools = await client.get_tools()
    sys_message = SystemMessage(
        content="あなたはMCPサーバーを使用するAIアシスタントです。"
                "Toolの結果を優先して回答として採用してください"
                "回答は日本語でお願いします。"
    )
    agent = create_react_agent(llm, tools, prompt=sys_message)
    return agent

# agentを用いてmessageを送信して返答をprint
async def send_message(agent, window: str, message: str) -> list[dict[str, str]]:
    cache_file = r"/root/message_cache/" + window
    message_history = []

    if window != "" and os.path.isfile(cache_file):
        with open(cache_file, "r", encoding="utf-8") as f:
            message_history = json.load(f)
    
    update_prompt = generate_rag_prompt.generate_rag_prompt(message)
    print(f"\n=== START Information ===\n{update_prompt[0]['content']}\n=== END Information ===", flush=True)
    message_history += update_prompt

    # ReAct エージェントは messages の履歴形式を期待
    result = await agent.ainvoke({"messages": message_history})
    results = print_messages(result)
    message_history += results

    # windowが指定されていた場合はキャッシュファイルに追記
    if window == "":
        return
    with open(cache_file, "w", encoding="utf-8") as f:
        json.dump(message_history, f, ensure_ascii=False, indent=4)

    return results

# ReAct agentからの返答を出力
def print_messages(result) -> list[dict[str, str]]:
    replies = []
    messages = result.get("messages", result)

    for msg in messages:
        msg_type = type(msg).__name__
        if not msg_type and hasattr(msg, "__class__"):
            msg_type = msg.__class__.__name__

        print(f"\n=== START {msg_type} ===")
        formated_msg = ""

        # print のコメントアウト後で消す
        keys = vars(msg).keys()
        if "name" in keys and msg.name != None and msg.name != "":
            # print(f"tool: {msg.name} ")
            formated_msg += f"tool: {msg.name} \n"
        if "content" in keys and msg.content != "":
            # print(msg.content)
            formated_msg += msg.content + "\n"
        if "tool_calls" in keys and len(msg.tool_calls) > 0:
            tool_messages = list(map(lambda x: f"{x['name']} {x['args']}", msg.tool_calls))
            # print("\n".join(tool_messages))
            formated_msg += "\n".join(tool_messages) + "\n"

        print(formated_msg)
        print(f"=== END {msg_type} ===")

        match msg_type:
            case "AIMessage":
                replies.append({"role": "assistant", "content": formated_msg})
            case "HumanMessage":
                replies.append({"role": "user", "content": formated_msg})
            case "ToolMessage":
                replies.append({"role": "tool", "content": formated_msg})
            case "SystemMessage":
                replies.append({"role": "system", "content": formated_msg})
            case _:
                replies.append({"role": "unknown", "content": formated_msg})

    return replies

async def main():
    # mcp_setting.jsonの読み込み
    mcp_setting_config = load_json_config().get("mcpServers", {})
    print(mcp_setting_config)

    # コマンドライン引数がある場合は送信するプロンプトを設定（存在しない場合は「こんにちは」を送信）
    prompt = "こんにちは"
    args = sys.argv
    if len(args) >= 3:
        window = args[1]
        prompt = " ".join(args[2:])

    # mcpクライアント、mcpホストの作成
    agent = await create_client(mcp_setting_config)
    # promptを送信、メッセージの出力
    await send_message(agent, window, prompt)

if __name__ == "__main__":
    asyncio.run(main())