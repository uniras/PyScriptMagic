import os
import sys
import time
import json
import socket
import subprocess
import IPython.display as display  # type: ignore  # noqa: F401
from typing import Callable
from http.server import SimpleHTTPRequestHandler, HTTPServer


# PyScriptのデフォルトバージョン
PYS_DEFAULT_VERSION = "2024.10.2"


# Google Colabで実行しているかどうかを判定
def is_google_colab() -> bool:
    try:
        import google.colab  # type: ignore  # noqa: F401
        return True
    except ImportError:
        return False


# ベースディレクトリを取得
def get_basedir() -> str:
    if is_google_colab():
        if os.path.exists("/content/drive/MyDrive"):
            return "/content/drive/MyDrive/Colab Notebooks"
        else:
            return "/content"
    else:
        return os.getcwd()


# 18000番台で空いているポート番号を取得
def find_free_port(start: int = 18000, end: int = 18099) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError("No free ports available")


# JavaScriptを実行してプロキシURLを取得
def get_server_url(port: int) -> str:
    if is_google_colab():
        from google.colab.output import eval_js  # type: ignore
        url = eval_js(f"google.colab.kernel.proxyPort({port})").strip("/")
    else:
        url = f"http://localhost:{port}"

    return url


# HTMLを生成
def generate_html(args: dict) -> str:
    # 引数の取得
    py_type = args.get("py_type", "mpy").lower()
    py_script = args.get("py_script", "")
    py_conf = args.get("py_conf", None)
    py_ver = args.get("py_ver", "none").lower()
    background = args.get("background", "white")
    js_src = args.get("js_src", None)
    add_src = args.get("add_src", None)
    add_script_code = args.get("add_script", None)
    add_css = args.get("add_css", None)
    add_style_code = args.get("add_style", None)

    # py_typeのチェック
    if py_type != "py" and py_type != "mpy":
        raise ValueError("Invalid type. Use py or mpy")

    # バージョンの指定がない場合はデフォルトバージョンを設定
    if py_ver == "none":
        py_ver = PYS_DEFAULT_VERSION

    # 外部css要素を生成
    if add_css is not None and isinstance(add_css, list):
        css_srctag = "\n".join([f'    <link rel="stylesheet" href="{src}" />' for src in add_css])
        css_srctag = css_srctag.rstrip("\n")
        css_srctag = f"\n{css_srctag}"
    else:
        css_srctag = ""

    # 追加スタイル要素を生成
    if add_style_code is not None and add_style_code != "":
        add_style = f"\n    <style>\n{add_style_code}\n    </style>"
    else:
        add_style = ""

    # 外部JavaSript要素を生成
    jsrcs = []

    if add_src is not None and isinstance(add_src, list):
        jsrcs = add_src

    if js_src is not None:
        try:
            jsrc = json.loads(js_src)
            if not isinstance(jsrc, list):
                raise ValueError("Invalid JSON List format for js_src")
            jsrcs.extend(jsrc)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON List format for js_src")

    if len(jsrcs) > 0:
        js_srctag = "\n".join([f'    <script src="{src}"></script>' for src in jsrcs])
        js_srctag = js_srctag.rstrip("\n")
        js_srctag = f"\n{js_srctag}"
    else:
        js_srctag = ""

    # 追加スクリプト要素を生成
    if add_script_code is not None and add_script_code != "":
        add_script = f"\n{add_script_code}"
    else:
        add_script = ""

    # py-config要素を生成
    if py_conf is not None:
        try:
            json.loads(py_conf)
        except json.JSONDecodeError:
            raise ValueError("Invalid JSON format for py_conf")
        py_config = f"\n    <{py_type}-config>{py_conf}\n    </{py_type}-config>"
    else:
        py_config = ""

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" crossorigin="anonymous" />
    <link rel="stylesheet" href="https://pyscript.net/releases/{py_ver}/core.css" />{css_srctag}{add_style}
    <script type="module" src="https://pyscript.net/releases/{py_ver}/core.js"></script>{js_srctag}
    <script type="module">
        const loading = document.getElementById('loading');
        addEventListener('{py_type}:ready', () => loading.close());
        loading.showModal();{add_script}
    </script>{py_config}
</head>
<body style="background:{background};">
    <dialog id="loading" style="outline:none; border:none; background:transparent;">
        <div class="spinner-border" role="status"></div>
        <span class="sr-only">Loading PyScript...</span>
    </dialog>
    <script type="{py_type}">
{py_script}
    </script>
</body>
</html>
    """.strip()


# サーバを起動する関数
def start_server(html: str, port: int) -> subprocess.Popen:
    # このファイルをPythonインタプリタで開いてサーバーを起動
    pycommand = "python" if sys.platform == "win32" else "python3"

    # Popenで標準入力を使用して実行
    process = subprocess.Popen(
        [pycommand, __file__, str(port)],
        stdin=subprocess.PIPE,
        text=True,
        encoding="utf-8"
    )

    process.stdin.write(html)
    process.stdin.close()

    # サーバーが起動するまで待機
    time.sleep(1)

    return process


# サーバーを停止する関数
def stop_server(process: subprocess.Popen) -> None:
    process.kill()


# PyScriptを実行するHTMLを生成してIFrameで表示
def run_pyscript(args: dict, genfunc: Callable[[dict], str] = None) -> None:
    # 引数の取得
    if not isinstance(args, dict):
        raise ValueError("Invalid args type. Use dict type.")
    width_str = args.get("width", "500")
    height_str = args.get("height", "500")
    htmlmode = args.get("htmlmode", False)
    py_file = args.get("py_file", None)
    dulation = args.get("dulation", 5)

    # 幅と高さの取得
    width = width_str if isinstance(width_str, int) else int(width_str) if isinstance(width_str, str) and width_str.isdecimal() else 500
    height = height_str if isinstance(height_str, int) else int(height_str) if isinstance(height_str, str) and height_str.isdecimal() else 500

    # Pythonファイルの読み込み
    if py_file is not None:
        with open(py_file, "r", encoding="utf-8") as f:
            args["py_script"] = f.read()

    # HTML生成
    if genfunc is not None:
        base_html = genfunc(args)
    else:
        base_html = generate_html(args)

    if htmlmode:
        # HTMLを表示
        display.display(display.Pretty(base_html))

    else:
        # 空きポートを取得
        port = find_free_port()

        # サーバーURLを取得
        url = get_server_url(port)

        # サーバーを起動
        process = start_server(base_html, port)

        # IFrameを使用して表示
        display.display(display.IFrame(src=url + "/", width=width, height=height))

        # 指定秒数待機
        time.sleep(dulation)

        # サーバーを停止
        stop_server(process)


# このファイルをPythonインタプリタで開いた場合の処理
def run_main_func(arg: list[str]) -> None:
    # カスタムハンドラクラス
    class CustomHandler(SimpleHTTPRequestHandler):
        def log_message(self, format, *args):
            # ログ出力を無効化（何も出力しない）
            pass

        def do_GET(self):
            # クエリパラメータを取り除く
            getpath = self.path.split("?")[0]

            if getpath == "/":
                # ルートパスにアクセスしたときは標準入力で渡されたHTMLを返す
                self.send_response(200)
                self.send_header("Content-type", "text/html")
                self.end_headers()

                self.wfile.write(self.server.pys_file.encode("utf-8"))
            else:
                # その他のリクエストは通常のファイルリクエストとして処理
                super().do_GET()

    # カスタムHTTPServerクラス
    class CustomHTTPServer(HTTPServer):
        def __init__(self, server_address, RequestHandlerClass, pys_file):
            super().__init__(server_address, RequestHandlerClass)
            self.pys_file = pys_file

    # 引数の取得
    if not isinstance(arg, list):
        raise ValueError("Invalid args type. Use list type.")

    port = int(arg[0]) if len(arg) > 0 else 18000

    # 標準入力からHTMLを取得
    file = sys.stdin.read()

    # カスタムHTTPServerクラスを使用し、引数を渡す
    server = CustomHTTPServer(('localhost', port), CustomHandler, file)

    # サーバーを起動
    server.serve_forever()


if __name__ == "__main__":
    run_main_func(sys.argv[1:])
