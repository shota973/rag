import sys
import json
import asyncio
import model
import generate_rag_prompt

from langchain_core.messages import SystemMessage
from langchain_mcp_adapters.client import MultiServerMCPClient
from langchain_ollama import ChatOllama
from langgraph.prebuilt import create_react_agent

# model.py で定義したCONFIG_PATHの内容を取得
def load_json_config(path=model.CONFIG_PATH):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

# ReAct agentからの返答を出力
def print_messages(result) -> list[list[str]]:
    messages = result.get("messages", result)
    if not isinstance(messages, list):
        print("messagesがリストではありません")
        return [["error", ""]]

    for msg in messages:
        message = ""
        msg_type = msg.get("type") if isinstance(msg, dict) else type(msg).__name__
        if not msg_type and hasattr(msg, "__class__"):
            msg_type = msg.__class__.__name__

        print(f"\n=== START {msg_type} ===")
        if isinstance(msg, dict):
            print("{")
            is_first_value = True
            for k, v in msg.items():
                if not is_first_value:
                    print(",")
                print(f"{k}: {v}")
                is_first_value = False
            print("}")

        else:
            keys = vars(msg).keys()
            if "name" in keys and msg.name != None and msg.name != "":
                print(f"tool: {msg.name} ")
            if "content" in keys and msg.content != "":
                print(msg.content)
            if "tool_calls" in keys and len(msg.tool_calls) > 0:
                tool_messages = list(map(lambda x: f"{x['name']} {x['args']}", msg.tool_calls))
                print("\n".join(tool_messages))
                
        print(f"=== END {msg_type} ===")

# clientやReAct agentの作成
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
async def send_message(agent, message: str) -> list[list[str]]:
    update_prompt = generate_rag_prompt.generate_rag_prompt(message)
    print(f"\n=== START Information ===\n{update_prompt[0]['content']}\n=== END Information ===", flush=True)

    # ReAct エージェントは messages の履歴形式を期待
    result = await agent.ainvoke({"messages": update_prompt})
    results = print_messages(result)
    return results

async def main():
    # mcp_setting.jsonの読み込み
    mcp_setting_config = load_json_config().get("mcpServers", {})
    print(mcp_setting_config)

    # コマンドライン引数がある場合は送信するプロンプトを設定（存在しない場合は「こんにちは」を送信）
    prompt = "こんにちは"
    args = sys.argv
    if len(args) >= 2:
        prompt = " ".join(args[1:])
    
    # mcpクライアント、mcpホストの作成
    agent = await create_client(mcp_setting_config)
    # promptを送信、メッセージのprint
    await send_message(agent, prompt)

if __name__ == "__main__":
    asyncio.run(main())