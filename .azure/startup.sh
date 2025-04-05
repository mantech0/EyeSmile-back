#!/bin/bash

echo "EyeSmile Backend Azure起動スクリプトを実行しています..."

# カレントディレクトリをアプリケーションのルートに設定
cd /home/site/wwwroot

# データベースパスを環境変数に設定
export SQLITE_PATH="/home/site/wwwroot/test.db"
echo "SQLiteパス: $SQLITE_PATH"

# 環境変数の設定
export PYTHONPATH=$PYTHONPATH:/home/site/wwwroot
export PORT=8000
export HOST=0.0.0.0
export WEBSITES_PORT=8000
export STORAGE_PATH="static/images"
export LOG_LEVEL="INFO"  # ログレベルを設定

# デバッグ情報
echo "現在の作業ディレクトリ: $(pwd)"
echo "環境変数一覧:"
printenv | grep -E "DB_|WEBSITE|PORT|HOST|STORAGE|APPLY"

# 静的ファイルディレクトリの作成
mkdir -p static/images
echo "静的ファイルディレクトリを作成しました: static/images"

# データベース設定値の確認
if [ -n "$DB_HOST" ]; then
    echo "データベースホスト: $DB_HOST"
else
    echo "警告: DB_HOSTが設定されていません"
fi

# SQLiteファイルの確認
if [ -f "test.db" ]; then
    echo "SQLiteデータベースファイルが存在します: test.db"
    sqlite3 test.db ".tables" || echo "SQLiteコマンドが実行できません"
else
    echo "SQLiteデータベースファイルが存在しません。初期化が必要です。"
fi

# データベース初期化スクリプトの実行
echo "データベース初期化を実行しています..."
python .azure/deploy_settings.py
DB_INIT_RESULT=$?
if [ $DB_INIT_RESULT -ne 0 ]; then
    echo "データベース初期化に失敗しました (終了コード: $DB_INIT_RESULT)。アプリケーションの起動を続行します。"
else
    echo "データベース初期化が完了しました。"
fi

# SQLiteファイルの権限設定
if [ -f "test.db" ]; then
    chmod 666 test.db
    echo "SQLiteファイルの権限を設定しました"
    ls -la test.db
fi

# マイグレーション実行フラグを設定
export APPLY_MIGRATIONS=true

# アプリケーションのデバッグモードを有効にする
export DEBUG=true

# アプリケーションの起動
echo "Gunicornでアプリケーションを起動します..."
gunicorn src.main:app --bind $HOST:$PORT --timeout 600 --workers 2 --threads 4 --log-level info 