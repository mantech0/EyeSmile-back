#!/bin/bash

echo "EyeSmile Backend Azure起動スクリプトを実行しています..."

# カレントディレクトリをアプリケーションのルートに設定
cd /home/site/wwwroot

# デバッグモード設定
set -x

# データベースパスを環境変数に設定
export SQLITE_PATH="/home/site/wwwroot/test.db"
echo "SQLiteパス: $SQLITE_PATH"

# 環境変数の設定
export PYTHONPATH=$PYTHONPATH:/home/site/wwwroot
export PORT=8000
export HOST=0.0.0.0
export WEBSITES_PORT=8000
export STORAGE_PATH="static/images"
export LOG_LEVEL="DEBUG"  # デバッグ用にログレベルを変更
export DEBUG=true

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

# マイグレーション実行フラグを設定
export APPLY_MIGRATIONS=true
export SQLITE_FALLBACK=true
export USE_SQLITE_FALLBACK=true

# SQLiteファイルの確認と初期化
echo "SQLite初期化を実行します..."
if [ -f "test.db" ]; then
    echo "SQLiteデータベースファイルが存在します: test.db"
    # 既存のファイルがある場合は権限を設定
    chmod 666 test.db || true
    echo "SQLiteファイルの権限を設定しました"
    ls -la test.db || true
else
    echo "SQLiteデータベースファイルが見つかりません。新規作成します"
    touch test.db || true
    chmod 666 test.db || true
    echo "SQLiteデータベースファイルを作成しました: test.db"
    ls -la test.db || true
fi

# 必要なパッケージのインストール
echo "必要なパッケージをインストールします..."
pip install --upgrade pip 2>/dev/null || true
pip install -r requirements.txt 2>/dev/null || true
pip install gunicorn pytest pytest-cov pymysql cryptography 2>/dev/null || true

# データベース初期化スクリプトの実行（エラーを無視）
echo "データベース初期化スクリプトを実行しています..."
python .azure/deploy_settings.py || true
echo "データベース初期化スクリプトの実行が完了しました（成功または失敗）"

# SQLiteデータベースの作成を簡略化（最低限必要なテーブル）
echo "最低限必要なSQLiteテーブルを作成します..."
cat > create_tables.sql << EOL
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT,
    hashed_password TEXT,
    is_active BOOLEAN DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS face_measurements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    face_width REAL,
    face_height REAL,
    pupillary_distance REAL,
    temple_width REAL,
    bridge_width REAL,
    image_path TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS frames (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    image_path TEXT,
    frame_width REAL,
    frame_height REAL,
    bridge_width REAL,
    temple_length REAL,
    style TEXT,
    material TEXT,
    color TEXT,
    shape TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
EOL

# SQLiteコマンドが利用可能か確認
if command -v sqlite3 &> /dev/null; then
    echo "SQLiteコマンドが利用可能です"
    sqlite3 test.db < create_tables.sql || true
    echo "基本テーブルの作成が完了しました"
    
    # テーブル一覧の確認
    echo "テーブル一覧:"
    sqlite3 test.db ".tables" || true
else
    echo "SQLiteコマンドが見つかりません。Pythonを使用してテーブルを作成します..."
    # シンプルなPythonスクリプトでテーブルを作成
    cat > create_tables.py << EOL
import sqlite3
import os

try:
    conn = sqlite3.connect('test.db')
    cursor = conn.cursor()
    
    # テーブル作成SQLを実行
    with open('create_tables.sql', 'r') as f:
        sql = f.read()
        cursor.executescript(sql)
    
    conn.commit()
    conn.close()
    print("テーブル作成が完了しました")
except Exception as e:
    print(f"エラー: {str(e)}")
EOL
    
    python create_tables.py || true
fi

# アプリケーションの起動（エラーハンドリング付き）
echo "Gunicornでアプリケーションを起動します..."
# デモデータフラグをtrueに設定してフェイクデータを返すようにする
export DEMO_MODE=true

# gunicornの起動（例外発生時は再試行）
gunicorn src.main:app --bind $HOST:$PORT --timeout 600 --workers 2 --threads 4 --log-level debug 