# obotai-webhook-example

## セットアップ

Python3.9でvenvを作成

```
python3.9 -m venv venv
```

activateしてvenvにライブラリをインストール

```
. venv/bin/activate
pip install -r requirements.txt
```

## 開発

ウェブフックはインターネット経由でアクセス可能なエンドポイントが必要なので、開発時は [ngrok](https://ngrok.com/) を利用することをおすすめします。
