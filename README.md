# PyScript Magic Command

## 概要

Jypyter(notebook/lab)・VSCodeまたはGoogle ColabでコードセルのPythonコードをPyScriptを使ってiframe(ブラウザ)上で実行するマジックコマンドです。

## 使い方

### マジックコマンドの追加

コードセルに以下のコードを貼り付けて実行しマジックコマンドを登録してください。カーネルやランタイムを再起動する度に再実行する必要があります。

```python
%pip install pysmagic
from pysmagic import register_pysmagic

register_pysmagic()
```

### マジックコマンドの使い方

コードセルの冒頭に以下のようにマジックコマンドを記述してください。実行するとアウトプットにiframeが表示されてその中でコードセルのコードがPyScriptで実行されます。

```python
%%run_iframe mpy 500 500 white '{}' '[]'

from pyscript import display
display("Hello, world!")
```

以下はブラウザ用JavaScriptライブラリのp5.jsを使って円を描画し、キーボードの矢印キーで移動させるサンプルです。

```python
%%run_iframe mpy 500 500 white '{}' '["https://cdn.jsdelivr.net/npm/p5@1.9.4/lib/p5.js"]'

import pyscript
import js

def start(p5):
    x = 100
    y = 100

    def setup():
        p5.createCanvas(300, 300)

    def draw():
        nonlocal x, y
        p5.background(128)
        p5.fill(255, 0, 0)
        p5.ellipse(x, y, 50, 50)

        if p5.keyIsDown(p5.LEFT_ARROW):
            x -= 1
        if p5.keyIsDown(p5.RIGHT_ARROW):
            x += 1
        if p5.keyIsDown(p5.UP_ARROW):
            y -= 1
        if p5.keyIsDown(p5.DOWN_ARROW):
            y += 1

    p5.setup = setup
    p5.draw = draw

p5run = js.window.Function("func", "new p5((p) => {func(p)})")
p5run(start)
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
- py_conf: PyScriptの設定を''で囲んだJSON文字列形式で指定します。デフォルトは{}です。
- js_src: 外部JavaScriptのURLを''で囲んだ文字列のJSON配列形式で指定します。デフォルトは[]です。
- version: PyScriptのバージョンを指定します

#### %%view_iframe

セル内のPythonコードをPyScriptを用いてiframe内で実行するために生成したHTMLを表示するマジックコマンド

引数は%%run_iframeと同じです。
