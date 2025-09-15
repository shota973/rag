import flet as ft
import time
import datetime
import model
import paramiko
import ssh_config

# メッセージに必要な情報を格納するためのクラス
class Message:
    def __init__(self, user_name: str, text: str):
        self.user_name = user_name
        self.text = text
        self.message_type = "chat"

# チャットUIの各メッセージを作成するクラス
class ChatMessage(ft.Row):
    def __init__(self, message: Message):
        super().__init__()
        self.vertical_alignment = ft.CrossAxisAlignment.START
        self.controls = [
            ft.CircleAvatar(
                content=ft.Text(self.get_initials(message.user_name)),
                color=ft.Colors.WHITE,
                bgcolor=self.get_avatar_color(message.user_name),
            ),
            ft.Column(
                [
                    ft.Text(message.user_name, weight="bold"),
                    ft.Text(message.text, selectable=True),
                ],
                expand=1,
                tight=True,
                width=100,
                spacing=5,
            ),
        ]

    def get_initials(self, user_name: str):
        if user_name:
            return user_name[:1].capitalize()
        else:
            return "Unknown"

    def get_avatar_color(self, user_name: str):
        colors_lookup = [
            ft.Colors.AMBER,
            ft.Colors.BLUE,
            ft.Colors.BROWN,
            ft.Colors.CYAN,
            ft.Colors.GREEN,
            ft.Colors.INDIGO,
            ft.Colors.LIME,
            ft.Colors.ORANGE,
            ft.Colors.PINK,
            ft.Colors.PURPLE,
            ft.Colors.RED,
            ft.Colors.TEAL,
            ft.Colors.YELLOW,
        ]
        return colors_lookup[hash(user_name) % len(colors_lookup)]


async def main(page: ft.Page):
    page.horizontal_alignment = ft.CrossAxisAlignment.STRETCH
    page.title = "AI Chat"

    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    # ssh_config.pyに記載した情報をもとにSSH接続を確立
    ssh.connect(ssh_config.host, username=ssh_config.username, password=ssh_config.password, timeout=120.0)
    
    # ssh先でコンテナを起動
    _, out, _ = ssh.exec_command(ssh_config.create_container_cmd, get_pty=True)
    for line in out:
        print(line)

    # メッセージ送信を行う関数
    def send_message(e):
        if new_message.value != "":
            # ユーザーメッセージをチャットに追加, formをクリア
            send_prompt = repr(new_message.value)
            add_message(
                Message(
                    "user",
                    send_prompt,
                )
            )
            new_message.value = ""
            new_message.focus()

            time.sleep(0.2) # delayがあったほうが見やすかったのでdelayをかけた
            loading_message = add_message(
                Message(
                    model.CHAT_MODEL,
                    "Loading...",
                )
            )
            # appコンテナのbashを開き、ユーザーの入力を付加してhost.pyを実行
            stdin, stdout, stderr = ssh.exec_command(ssh_config.enter_app_cmd, get_pty=True)
            stdin.write(ssh_config.run_app_cmd(window_date.value, send_prompt))
            stdin.close()
                
            chat.controls.remove(loading_message)
            errorMes = [line.strip() for line in stderr]
            outMes = [line.strip() for line in stdout]
            print(errorMes)
            print(outMes)

            # 標準出力から"=== START ～～ ==="などを目印にメッセージを抽出
            start_aiMeses = [i + 1 for i, x in enumerate(outMes) if x == "=== START AIMessage ==="]
            end_aiMeses = [i for i, x in enumerate(outMes) if x == "=== END AIMessage ==="]
            aiMeses = [{"name": model.CHAT_MODEL, "index": start_aiMeses[i], "content": outMes[start_aiMeses[i]:end_aiMeses[i]]} for i in range(min(len(start_aiMeses), len(end_aiMeses)))]

            start_toolMeses = [i + 1 for i, x in enumerate(outMes) if x == "=== START ToolMessage ==="]
            end_toolMeses = [i for i, x in enumerate(outMes) if x == "=== END ToolMessage ==="]
            toolMeses = [{"name": "tool message", "index": start_toolMeses[i], "content": outMes[start_toolMeses[i]:end_toolMeses[i]]} for i in range(min(len(start_toolMeses), len(end_toolMeses)))]

            start_infomations = [i + 1 for i, x in enumerate(outMes) if x == "=== START Information ==="]
            end_infomations = [i for i, x in enumerate(outMes) if x == "=== END Information ==="]
            infomations = [{"name": "RAG information", "index": start_infomations[i], "content": outMes[start_infomations[i]:end_infomations[i]]} for i in range(min(len(start_infomations), len(end_infomations)))]

            # メッセージをindexでソートして標準出力の順番通りにチャットに追加
            messages = aiMeses + toolMeses + infomations
            sorted_messages = sorted(messages, key=lambda x: x["index"])

            # 各メッセージをチャットに追加
            if len(errorMes) > 0:
                add_message(
                    Message(
                        "error message",
                        "\n".join(errorMes),
                    )
                )
            for mes in sorted_messages:
                add_message(
                    Message(
                        mes["name"],
                        "\n".join(mes["content"]),
                    )
                )
            page.update()

    # チャットにメッセージを追加する関数
    def add_message(message: Message) -> ChatMessage:
        m = ChatMessage(message)
        chat.controls.append(m)
        page.update()
        return m

    # SSH切断、コンテナの停止用の関数
    def close_ssh_client(e):
        close_popup.content = ft.Text("loading...")
        page.update()

        _, _, closeerr = ssh.exec_command(ssh_config.stop_container_cmd, get_pty=True)
        errMes = [line.strip() for line in closeerr]
        if len(errMes) > 0:
            close_popup.title = ft.Text("ERROR occurred")
            close_popup.content = ft.Text(" ".join(errMes))
        ssh.close()

        # 正常に切断、コンテナ停止できた場合、ダイアログを閉じてチャットにメッセージを追加
        close_dlg(e)
        add_message(
            Message(
                "system",
                "ssh接続が切断されました"
            )
        )
        close_button.icon_color = ft.Colors.SECONDARY
        page.update()

    # ssh切断時に表示するダイアログを閉じる関数
    def close_dlg(e):
        close_popup.open = False
        page.update()

    # window名を日付で設定
    window_date = ft.Text(datetime.datetime.now().strftime("%Y/%m/%d-%H:%M:%S"))

    # メッセージ一覧を表示する要素
    chat = ft.ListView(
        expand=1,
        spacing=10,
        auto_scroll=True,
    )

    # メッセージ入力フォーム
    new_message = ft.TextField(
        hint_text="shift + enterで改行",
        autofocus=True,
        shift_enter=True,
        min_lines=1,
        max_lines=5,
        filled=True,
        expand=1,
        on_submit=send_message,
    )

    # SSH切断、コンテナ停止用のダイアログとボタン
    close_popup = ft.AlertDialog(
        modal=True,
        title=ft.Text("Down container and Close SSH"),
        content=ft.Text("Is it okay to shut down the container and disconnect SSH?"),
        actions=[
            ft.TextButton("Yes", on_click=close_ssh_client),
            ft.TextButton("No", on_click=close_dlg),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
    )

    # SSH切断、コンテナ停止用のpopupを表示するボタン
    close_button = ft.IconButton(
        icon=ft.Icons.DESKTOP_ACCESS_DISABLED_ROUNDED,
        icon_color=ft.Colors.RED,
        tooltip="Close SSH",
        on_click=lambda e: page.open(close_popup),
    )

    # 各要素からページを作成
    page.add(
        window_date,
        ft.Container(
            content=chat,
            border=ft.border.all(1, ft.Colors.OUTLINE),
            border_radius=5,
            padding=10,
            expand=1,
        ),
        ft.Row(
            [
                new_message,
                close_button,
            ]
        ),
    )

if __name__ == "__main__":
    ft.app(target=main)