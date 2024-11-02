import shlex
import IPython.core.magic as magic  # type: ignore  # noqa: F401
from .pysrunner import run_pyscript


# magic commandを登録する関数
def register_pysmagic():
    from IPython import get_ipython  # type: ignore  # noqa: F401
    ipy = get_ipython()
    ipy.register_magic_function(runpys)
    ipy.register_magic_function(genpys)
    print("Registered PyScript magic commands.")


# iframe内でPyScriptを実行するマジックコマンド
@magic.register_cell_magic
def runpys(line, cell):
    """
    セル内のPythonコードをPyScriptを用いてiframe内で実行するマジックコマンド

    Usage:
        %%runpys [width] [height] [background] [py_type] [py_conf] [js_src] [py_ver]

    Args:
        width: iframeの幅を指定します。デフォルトは500です。
        height: iframeの高さを指定します。デフォルトは500です。
        background: iframeの背景色を指定します。デフォルトはwhiteです。
        py_type: 実行するPythonの種類。pyまたはmpyを指定します。pyはCPython互換のPyodide、mpyはMicroPytonで実行します。デフォルトはmpyです。
        py_conf: PyScriptの設定を''で囲んだJSON形式で指定します。デフォルトは{}です。
        js_src: 外部JavaScriptのURLを''で囲んだ文字列のJSON配列形式で指定します。デフォルトは[]です。
        py_ver: PyScriptのバージョンを指定します.
    """
    # 引数のパース
    args = parse_pys_args(line)
    args["py_script"] = cell
    args["htmlmode"] = False

    # PyScriptを実行
    run_pyscript(args)


@magic.register_cell_magic
def genpys(line, cell):
    """
    セル内のPythonコードをPyScriptを用いてiframe内で実行するために生成したHTMLを表示するマジックコマンド
    """
    # 引数のパース
    args = parse_pys_args(line)
    args["py_script"] = cell
    args["htmlmode"] = True

    # PyScriptを実行
    run_pyscript(args)


def parse_pys_args(line):
    # 引数のパース
    line_args = shlex.split(line)
    args = {}
    args["width"] = line_args[0] if len(line_args) > 0 else "500"
    args["height"] = line_args[1] if len(line_args) > 1 else "500"
    args["background"] = line_args[2] if len(line_args) > 2 else "white"
    args["py_type"] = line_args[3].lower() if len(line_args) > 3 else "mpy"
    args["py_conf"] = line_args[4] if len(line_args) > 4 and line_args[4] != "{}" else None
    args["js_src"] = line_args[5] if len(line_args) > 5 and line_args[5] != "[]" else None
    args["py_ver"] = line_args[6] if len(line_args) > 6 and line_args[6].lower() != "none" else None

    return args
