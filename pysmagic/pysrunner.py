import os
import sys
import time
import json
import socket
import subprocess
import textwrap
import IPython.display as display  # type: ignore  # noqa: F401
from IPython import get_ipython  # type: ignore
from typing import Callable
from http.server import SimpleHTTPRequestHandler, HTTPServer
from collections.abc import Mapping, Sequence


# PyScriptのデフォルトバージョン
__PYS_DEFAULT_VERSION = '2025.3.1'

# 一時サーバーのポート範囲
__DEFAULT_SERVER_PORT_START = 18000
__DEFAULT_SERVER_PORT_END = 18099

# デフォルトの画面サイズ
__DEFAULT_WIDTH = 500
__DEFAULT_HEIGHT = 500

# PyScriptモードのリスト
__PYS_MODES = ['py', 'mpy', 'py-game']


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
        if os.path.exists('/content/drive/MyDrive'):
            return '/content/drive/MyDrive/Colab Notebooks'
        else:
            return '/content'
    else:
        return os.getcwd()


# 設定したポート番号内で空いているポート番号を取得
def find_free_port(start: int = __DEFAULT_SERVER_PORT_START, end: int = __DEFAULT_SERVER_PORT_END) -> int:
    for port in range(start, end):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('localhost', port)) != 0:
                return port
    raise RuntimeError('No free ports available')


# JavaScriptを実行してプロキシURLを取得
def get_server_url(port: int) -> str:
    if is_google_colab():
        from google.colab.output import eval_js  # type: ignore
        url = eval_js(f"google.colab.kernel.proxyPort({port})").strip('/')
    else:
        url = f"http://localhost:{port}"

    return url


# 値がJSONに変換可能かどうかを判定する関数
def is_json_serializable(value):
    if isinstance(value, (str, int, float, bool, type(None))):  # 基本型
        return True

    if isinstance(value, Mapping):  # 辞書型
        return all(is_json_serializable(k) and is_json_serializable(v) for k, v in value.items())

    if isinstance(value, Sequence) and not isinstance(value, (str, bytes)):  # リストやタプル
        return all(is_json_serializable(item) for item in value)

    return False  # その他は不可


# グローバル変数からJSON変換可能なものだけ取り出す
def get_serializable_globals():
    cell_globals = {
        key: value
        for key, value in get_ipython().user_ns.items()
        if not key.startswith('__')  # 特殊変数を除外
        and not callable(value)  # 関数を除外
        and not key.startswith('_')  # セルの履歴（_i, _ii など）を除外
        and not key.startswith('In')
        and not key.startswith('Out')
        and not key == 'pys_args'  # pys_argsを除外
    }

    # キーが文字列で、値がJSON変換可能なものだけ取り出す
    return {key: value for key, value in cell_globals.items() if isinstance(key, str) and is_json_serializable(value)}


# リストを結合する関数
def extend_list(src, dst):
    if isinstance(src, list) and isinstance(dst, list):
        result = dst.copy()
        result.extend(src)
        return result
    elif isinstance(dst, list):
        result = dst.copy()
        result.append(src)
        return result
    elif isinstance(src, list):
        result = [dst]
        result.extend(src)
        return result
    else:
        return [dst, src]


# 辞書をマージする関数
def merge_dict(src, dst):
    for key in src:
        if key in dst:
            if isinstance(src[key], dict) and isinstance(dst[key], dict):
                dst[key] = merge_dict(src[key], dst[key])
            elif isinstance(dst[key], list):
                dst[key] = extend_list(src[key], dst[key])
        else:
            dst[key] = src[key]
    return dst


# HTMLを生成
def generate_html(args: dict) -> str:
    # 引数の取得
    width = args.get('width_value', __DEFAULT_WIDTH)
    height = args.get('height_value', __DEFAULT_HEIGHT)
    py_type_arg = args.get('py_type', 'mpy')
    py_script = args.get('py_script', '')
    py_conf = args.get('py_conf', None)
    py_ver = args.get('py_ver', 'none')
    py_val = args.get('py_val', None)
    background = args.get('background', 'white')
    js_src = args.get('js_src', None)
    add_src = args.get('add_src', None)
    add_script_code = args.get('add_script', None)
    add_css = args.get('add_css', None)
    add_style_code = args.get('add_style', None)
    viewport = args.get('viewport', 'width=device-width, initial-scale=1.0')

    # py_typeのチェック
    if not isinstance(py_type_arg, str) or (py_type_arg.lower() not in __PYS_MODES):
        raise ValueError('Invalid type. Use py or mpy or py-game.')
    else:
        py_type = py_type_arg.lower()

    # バージョンの指定がない場合はデフォルトバージョンを設定
    if not isinstance(py_ver, str) or py_ver.lower() == 'none':
        py_ver = __PYS_DEFAULT_VERSION

    # 外部css要素を生成
    if add_css is not None and isinstance(add_css, list):
        css_srctag = '\n'.join([f"""    <link rel="stylesheet" href="{src}" />""" for src in add_css])
        css_srctag = css_srctag.rstrip('\n')
        css_srctag = f"\n{css_srctag}"
    else:
        css_srctag = ''

    # 追加スタイル要素を生成
    if add_style_code is not None and add_style_code != '':
        add_style_str = textwrap.indent(textwrap.dedent(add_style_code), '        ')
        add_style = f"\n{add_style_str}\n\n"
    else:
        add_style = ''

    # 外部JavaSript要素を生成
    jsrcs = []

    if add_src is not None and isinstance(add_src, list):
        jsrcs = add_src

    if js_src is not None:
        try:
            jsrc = json.loads(js_src)
            if not isinstance(jsrc, list):
                raise ValueError('Invalid JSON List format for js_src')
            jsrcs.extend(jsrc)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON List format for js_src')

    if len(jsrcs) > 0:
        js_srctag = '\n'.join([f"""    <script src="{src}"></script>""" for src in jsrcs])
        js_srctag = js_srctag.rstrip('\n')
        js_srctag = f"\n{js_srctag}"
    else:
        js_srctag = ''

    # 追加スクリプト要素を生成
    if add_script_code is not None and add_script_code != '':
        add_script_str = textwrap.indent(textwrap.dedent(add_script_code), '        ')
        add_script = f"\n\n{add_script_str}"
    else:
        add_script = ''

    # py-config属性を生成
    if py_conf is not None:
        try:
            json.loads(py_conf)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON format for py_conf')
        py_conf_str = py_conf.replace('\r', '').replace('\n', '')
        py_config = f" config='{py_conf_str}'"
    else:
        py_config = ''

    # py-val要素とJSON変換可能なグローバル変数をJSON文字列に変換して生成
    py_val_base = get_serializable_globals()

    if isinstance(py_val, str) and py_val != '':
        try:
            py_val_data = json.loads(py_val)
            py_val_base.update(py_val_data)
        except json.JSONDecodeError:
            raise ValueError('Invalid JSON format for py_val')

    py_val_base.update({'width': width, 'height': height})

    py_val_json = json.dumps(py_val_base)

    # py-gameの場合はキャンバス要素を生成
    if py_type == 'py-game':
        py_game_canvas = '\n    <canvas id="canvas"></canvas>'
    else:
        py_game_canvas = ''

    return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="{viewport}" />

    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/@ionic/core/css/ionic.bundle.css" />
    <link rel="stylesheet" href="https://pyscript.net/releases/{py_ver}/core.css" />{css_srctag}
    <style>{add_style}
        body {{
            background: {background};
        }}

        #loading {{
            color: {background};
            filter: invert(100%) grayscale(100%) contrast(100);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
    </style>

    <script type="module" src="https://pyscript.net/releases/{py_ver}/core.js"></script>
    <script type="module" src="https://cdn.jsdelivr.net/npm/@ionic/core/dist/ionic/ionic.esm.js"></script>
    <script type="module" src="https://cdn.jsdelivr.net/npm/ionicons@latest/dist/ionicons/ionicons.esm.js"></script>{js_srctag}
    <script type="module">
        globalThis.pys = JSON.parse(`{py_val_json}`);
        document.getElementById('loading').classList.add('ion-text-center', 'ion-justify-content-center', 'ion-align-items-center', 'ion-padding');{add_script}
    </script>
</head>
<body style="background:{background};">
    <div id="loading">
        <ion-spinner name="crescent"></ion-spinner><span>Loading PyScript...</span>
    </div>{py_game_canvas}
    <script type="{py_type}"{py_config}>
import js
js.document.getElementById('loading').style.display = 'none'
{py_script}
    </script>
</body>
</html>
    """.strip()


# サーバを起動する関数
def start_server(html: str, port: int) -> subprocess.Popen:
    # このファイルをPythonインタプリタで開いてサーバーを起動
    pycommand = 'python' if sys.platform == 'win32' else 'python3'

    # Popenで標準入力を使用して実行
    process = subprocess.Popen(
        [pycommand, __file__, str(port)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        encoding='utf-8'
    )

    # サーバーが起動するまで待機
    time.sleep(1)

    if process.poll() is None:
        # サーバー起動に成功したら生成したHTMLを標準入力で渡す
        process.stdin.write(html)
        process.stdin.close()
        return process
    else:
        # 起動に失敗したらエラーを表示
        print('Server start failed. return code:', process.poll())
        print(process.stdout)
        print(process.stderr)
        return None


# サーバーを停止する関数
def stop_server(process: subprocess.Popen) -> None:
    process.kill()


# PyScriptを実行するHTMLを生成してIFrameで表示
def run_pyscript(args: dict, genfunc: Callable[[dict], str] = None) -> None:
    # 引数の取得
    if not isinstance(args, dict):
        raise ValueError('Invalid args type. Use dict type.')
    width_str = args.get('width', str(__DEFAULT_WIDTH))
    height_str = args.get('height', str(__DEFAULT_HEIGHT))
    htmlmode = args.get('htmlmode', False)
    py_file = args.get('py_file', None)
    dulation = args.get('dulation', 5)

    # 幅と高さの取得
    width = width_str if isinstance(width_str, int) else int(width_str) if isinstance(width_str, str) and width_str.isdecimal() else __DEFAULT_WIDTH
    height = height_str if isinstance(height_str, int) else int(height_str) if isinstance(height_str, str) and height_str.isdecimal() else __DEFAULT_HEIGHT
    args['width_value'] = width
    args['height_value'] = height

    # Pythonファイルの読み込み
    if py_file is not None:
        with open(py_file, 'r', encoding='utf-8') as f:
            args['py_script'] = f.read()

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

        if process is not None:
            # IFrameを使用して表示
            display.display(display.IFrame(src=url + '/', width=width, height=height))

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
            # クエリパラメータを取り除く(Colab対応)
            getpath = self.path.split('?')[0]

            if getpath == '/':
                # ルートパスにアクセスしたときは標準入力で渡されたHTMLを返す
                self.send_response(200)
                self.send_header('Content-type', 'text/html')
                self.end_headers()

                self.wfile.write(self.server.pys_file.encode('utf-8'))
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
        raise ValueError('Invalid args type. Use list type.')

    port = int(arg[0]) if len(arg) > 0 and arg[0].isdecimal() else __DEFAULT_SERVER_PORT_START

    # 標準入力からHTMLを取得
    file = sys.stdin.read()

    # カスタムHTTPServerクラスを使用し、引数を渡す
    server = CustomHTTPServer(('localhost', port), CustomHandler, file)

    # サーバーを起動
    server.serve_forever()


if __name__ == '__main__':
    run_main_func(sys.argv[1:])
