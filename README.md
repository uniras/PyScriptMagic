# PyScript Magic Command

## 概要

Jypyter(notebook/lab)またはGoogle ColabでコードセルのコードをPyScriptを使ってiframeで実行するマジックコマンドです。

## インストール

psmagic.pyをダウンロードして、Jupyterの場合は使用するノートブックと同じディレクトリに、
Google Colabの場合は/contentディレクトリまたはGoogle DriveのColab Notebooksディレクトリ(/content/drive/MyDrive/Colab Notebooks/)にアップロードしてください。

## 使い方

### マジックコマンドの追加

コードセルに以下のコードを貼り付けて実行しマジックコマンドを登録してください。カーネルやランタイムを再起動する度に再実行する必要があります。

```python
# Google Colab用(psmagic.pyをアップロードしたパスに合わせて変更して下さい)
import sys
sys.path.append("/content/drive/MyDrive/Colab Notebooks")
from psmagic import register_psmagic

# マジックコマンドの登録
register_psmagic()
```

### マジックコマンドの使い方

コードセルの冒頭に以下のようにマジックコマンドを記述してください。実行するとアウトプットにiframeが表示されてその中でコードセルのコードがPyScriptで実行されます。

```python
%%run_iframe mpy 500 500 white '{}' '[]'

from pyscript import display
display("Hello, world!")
```

### マジックコマンド

#### %%run_iframe

コードセルのコードをPyScriptを使ってiframe内で実行します。

```jupyter
%%run_iframe [type] [width] [height] [background] [py_conf] [js_src] [version]
```

- type: 実行するPythonの種類。pyまたはmpyを指定します。pyは CPython互換のPyodide、mpyはMicroPytonで実行します。デフォルトはmpyです。
- width: iframeの幅を指定します。デフォルトは500です。
- height: iframeの高さを指定します。デフォルトは500です。
- background: iframeの背景色を指定します。デフォルトはwhiteです。
- py_conf: PyScriptの設定を''で囲んだJSON形式で指定します。デフォルトは{}です。
- js_src: 外部JavaScriptのURLを''で囲んだ文字列のJSON配列形式で指定します。デフォルトは[]です。
- version: PyScriptのバージョンを指定します

#### %%view_iframe

セル内のPythonコードをPyScriptを用いてiframe内で実行するために生成したHTMLを表示するマジックコマンド

引数は%%run_iframeと同じです。
