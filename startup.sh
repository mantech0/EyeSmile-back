#!/bin/bash

# アプリケーションのルートディレクトリに移動
cd "$HOME/site/wwwroot"

# 環境変数の設定
echo "環境設定を行っています..."
export PYTHONPATH=$PYTHONPATH:$(pwd)

# 静的ディレクトリ作成
echo "静的ディレクトリを作成しています..."
mkdir -p static/images

# リポジトリから画像をコピー
if [ -d "$HOME/site/repository/static/images" ]; then
    echo "リポジトリから画像をコピーしています..."
    cp -r $HOME/site/repository/static/images/* static/images/
fi

# 依存関係のインストール
echo "依存パッケージを確認しています..."
pip install -r requirements.txt

# データベースマイグレーションの実行
echo "データベースマイグレーションを実行しています..."
export APPLY_MIGRATIONS=true

# ファイル一覧を確認（デバッグ用）
echo "静的ファイルディレクトリの内容:"
ls -la static/images/

# サーバーの起動
echo "アプリケーションを起動します..."
gunicorn src.main:app -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000 --timeout 180

