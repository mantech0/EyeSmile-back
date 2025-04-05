#!/bin/bash

echo "EyeSmile Backend Azure起動スクリプトを実行しています..."

# カレントディレクトリをアプリケーションのルートに設定
cd /home/site/wwwroot

# 環境変数の設定
export PYTHONPATH=$PYTHONPATH:/home/site/wwwroot
export PORT=8000
export HOST=0.0.0.0
export WEBSITES_PORT=8000
export STORAGE_PATH="static/images"

# 静的ファイルディレクトリの作成
mkdir -p static/images
echo "静的ファイルディレクトリを作成しました: static/images"

# データベース初期化スクリプトの実行
echo "データベース初期化を実行しています..."
python .azure/deploy_settings.py
if [ $? -ne 0 ]; then
    echo "データベース初期化に失敗しました。それでもアプリケーションの起動を続行します。"
fi

# マイグレーション実行フラグを設定
export APPLY_MIGRATIONS=true

# アプリケーションのデバッグモードを有効にする
export DEBUG=true

# アプリケーションの起動
echo "Gunicornでアプリケーションを起動します..."
gunicorn src.main:app --bind $HOST:$PORT --timeout 600 --workers 2 --threads 4 --log-level info 