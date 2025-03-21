import shlex
import IPython.core.magic as magic  # type: ignore
from IPython import get_ipython  # type: ignore
from .pysrunner import run_pyscript, merge_dict


# magic commandを登録する関数
def register_pysmagic():
    ipy = get_ipython()
    ipy.register_magic_function(runpys)
    ipy.register_magic_function(genpys)
    print('Registered PyScript magic commands.')


# iframe内でPyScriptを実行するマジックコマンド
@magic.register_cell_magic
def runpys(line, cell):
    """
    セル内のPythonコードをPyScriptを用いてiframe内で実行するマジックコマンド

    Usage:
        %%runpys [width] [height] [background] [py_type] [py_val] [py_conf] [js_src] [py_ver] [viewport]

    Args:
        width: iframeの幅を指定します。デフォルトは500です。
        height: iframeの高さを指定します。デフォルトは500です。
        background: iframeの背景色を指定します。デフォルトはwhiteです。
        py_type: 実行するPythonの種類。pyまたはmpyまたはpy-gameを指定します。pyとpy-gameはCPython互換のPyodide、mpyはMicroPytonで実行します。py-gameではゲームライブラリとしてPygame-ceを使えるようになります。デフォルトはmpyです。
        py_val: PyScriptに渡すデータを''で囲んだJSON文字列形式で設定します。デフォルトは'{}'です
        py_conf: PyScriptの設定を''で囲んだJSON文字列形式で指定します。デフォルトは'{}'です。
        js_src: 外部JavaScriptのURLを''で囲んだ文字列のJSON配列形式で指定します。デフォルトは'[]'です。
        py_ver: PyScriptのバージョンを指定します.
        viewport: viewportの設定を指定します。デフォルトは'width=device-width, initial-scale=1.0'です。
    """
    # 引数のパース
    args = parse_pys_args(line)
    args['py_script'] = cell
    args['htmlmode'] = False

    # PyScriptを実行
    run_pyscript(args)


@magic.register_cell_magic
def genpys(line, cell):
    """
    セル内のPythonコードをPyScriptを用いてiframe内で実行するために生成したHTMLを表示するマジックコマンド
    """
    # 引数のパース
    args = parse_pys_args(line)
    args['py_script'] = cell
    args['htmlmode'] = True

    # PyScriptを実行
    run_pyscript(args)


def default_args():
    return {
        'width': '500',
        'height': '500',
        'background': 'white',
        'py_type': 'mpy',
        'py_val': None,
        'py_conf': None,
        'js_src': None,
        'py_ver': 'none',
        'viewport': 'width=device-width, initial-scale=1.0',
    }


def parse_pys_args(line):
    # 引数のパース
    line_args = shlex.split(line)

    def_args = default_args()

    ipython_user_ns = get_ipython().user_ns

    if len(line_args) == 0:
        if 'pys_args' in ipython_user_ns.keys() and isinstance(ipython_user_ns['pys_args'], dict):
            args = merge_dict(def_args, ipython_user_ns['pys_args'])
        else:
            args = def_args
    else:
        args = {}
        args['width'] = line_args[0] if len(line_args) > 0 else def_args['width']
        args['height'] = line_args[1] if len(line_args) > 1 else def_args['height']
        args['background'] = line_args[2] if len(line_args) > 2 else def_args['background']
        args['py_type'] = line_args[3] if len(line_args) > 3 else def_args['py_type']
        args['py_val'] = line_args[4] if len(line_args) > 4 and line_args[4] != '{}' else def_args['py_val']
        args['py_conf'] = line_args[5] if len(line_args) > 5 and line_args[5] != '{}' else def_args['py_conf']
        args['js_src'] = line_args[6] if len(line_args) > 6 and line_args[6] != '[]' else def_args['js_src']
        args['py_ver'] = line_args[7] if len(line_args) > 7 else def_args['py_ver']
        args['viewport'] = line_args[8] if len(line_args) > 8 else def_args['viewport']

    return args
