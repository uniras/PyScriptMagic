import tempfile
import os
import socket
import threading
import subprocess
import time
import json
import IPython.display as display  # type: ignore  # noqa: F401


# PyScriptのデフォルトバージョン
PYS_DEFAULT_VERSION = "2024.10.1"


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


# サーバを起動する関数
def start_server_func(file_path: str, port: int) -> None:
    TIMEOUT = 30  # サーバーのタイムアウト（秒）
    server_process = subprocess.Popen(["python", "-m", "http.server", f"{port}"])
    time.sleep(TIMEOUT)
    server_process.terminate()  # プロセスの終了
    os.remove(file_path)


# サーバを別スレッドで起動
def start_server(file_path: str, port: int) -> None:
    thread = threading.Thread(target=start_server_func, args=(file_path, port))
    thread.daemon = True
    thread.start()
    time.sleep(1)  # サーバーが起動するまで待つ


# HTMLを生成
def generate_html(args: dict) -> str:
    # 引数の取得
    py_type = args.get("py_type", "mpy")
    py_script = args.get("py_script", "")
    py_conf = args.get("py_conf", None)
    py_ver = args.get("py_ver", None)
    background = args.get("background", "white")
    js_src = args.get("js_src", None)
    add_src = args.get("add_src", None)
    add_script = args.get("add_script", None)
    add_css = args.get("add_css", None)
    add_style = args.get("add_style", None)

    # py_typeのチェック
    if py_type != "py" and py_type != "mpy":
        raise ValueError("Invalid type. Use py or mpy")

    # バージョンの指定がない場合はデフォルトバージョンを設定
    if py_ver is None:
        py_ver = PYS_DEFAULT_VERSION

    # 外部css要素を生成
    if add_css is not None and isinstance(add_css, list):
        css_srctag = "\n".join([f'    <link rel="stylesheet" href="{src}" />' for src in add_css])
        css_srctag = css_srctag.rstrip("\n")
        css_srctag = f"\n{css_srctag}"
    else:
        css_srctag = ""

    # 追加スタイル要素を生成
    if add_style is not None and add_style != "":
        add_style = f"\n    <style>\n{add_style}\n    </style>"
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
    if add_script is not None and add_script != "":
        add_script = f"\n{add_script}"
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


# Pyscriptを実行するHTMLを生成してIFrameで表示
def run_pyscript(args: dict) -> None:
    # 引数の取得
    if not isinstance(args, dict):
        raise ValueError("Invalid args type. Use dict type.")
    width = args.get("width", 500)
    height = args.get("height", 500)
    htmlmode = args.get("htmlmode", False)

    # HTML生成
    base_html = generate_html(args)

    if htmlmode:
        # HTMLを表示
        display.display(display.Pretty(base_html))

    else:
        # 一時ファイルを作成
        basedir = get_basedir()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".html", delete=False, dir=basedir, encoding="utf-8") as f:
            f.write(base_html)
            temp_html_path = f.name

        # サーバーを起動
        port = find_free_port()

        # サーバーURLを取得
        url = get_server_url(port)

        # サーバーを起動
        start_server(temp_html_path, port)

        # ファイル名をURLに追加
        htmlurl = url + "/" + os.path.basename(temp_html_path)

        # IFrameを使用して表示
        display.display(display.IFrame(src=htmlurl, width=width, height=height))
