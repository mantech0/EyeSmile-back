"""
Azureデプロイ用の設定と初期化スクリプト
"""

import os
import sys
import traceback
import logging
import sqlite3
from pathlib import Path

# パスの設定
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)  # 親ディレクトリをパスに追加

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database():
    """
    データベースの初期化を行います。
    SQLiteへのフォールバック時にテーブルが作成されることを確認します。
    """
    try:
        # カレントディレクトリをルートディレクトリに設定
        root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        os.chdir(root_dir)
        logger.info(f"現在の作業ディレクトリ: {os.getcwd()}")
        
        # SQLiteデータベースファイルのパス
        db_path = os.path.join(root_dir, 'test.db')
        logger.info(f"SQLiteデータベースパス: {db_path}")
        
        # SQLiteデータベースファイルが存在するか確認
        if os.path.exists(db_path):
            logger.info("SQLiteデータベースファイルが存在します")
            # テーブルの存在確認と作成
            create_sqlite_tables(db_path)
        else:
            logger.warning("SQLiteデータベースファイルが存在しません。新規作成します")
            # 空のデータベースファイルを作成
            with open(db_path, 'w') as f:
                pass
            # テーブル作成
            create_sqlite_tables(db_path)
            
        # 権限設定
        try:
            os.chmod(db_path, 0o666)  # 読み書き権限を全ユーザーに付与
            logger.info(f"SQLiteファイルの権限を設定しました: {oct(os.stat(db_path).st_mode)[-3:]}")
        except Exception as e:
            logger.error(f"SQLiteファイルの権限設定に失敗: {str(e)}")
        
        return True
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def create_sqlite_tables(db_path):
    """SQLiteデータベースに必要なテーブルを作成します"""
    try:
        # SQLiteデータベースへの接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 既存のテーブルを確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"既存のテーブル: {existing_tables}")
        
        # 作成すべきテーブルの定義
        tables = {
            "users": """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email VARCHAR(255) NOT NULL,
                    gender VARCHAR(10) NOT NULL,
                    birth_date DATE NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """,
            "style_questions": """
                CREATE TABLE IF NOT EXISTS style_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_type VARCHAR(50) NOT NULL,
                    question_text VARCHAR(500) NOT NULL,
                    display_order INTEGER NOT NULL,
                    options TEXT,
                    multiple_select BOOLEAN DEFAULT 0
                )
            """,
            "preferences": """
                CREATE TABLE IF NOT EXISTS preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category VARCHAR(50) NOT NULL,
                    preference_value VARCHAR(100) NOT NULL,
                    display_name VARCHAR(255) NOT NULL,
                    description TEXT,
                    color_code VARCHAR(7)
                )
            """,
            "user_responses": """
                CREATE TABLE IF NOT EXISTS user_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    question_id INTEGER NOT NULL,
                    selected_preference_id INTEGER NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (question_id) REFERENCES style_questions (id),
                    FOREIGN KEY (selected_preference_id) REFERENCES preferences (id)
                )
            """,
            "face_measurements": """
                CREATE TABLE IF NOT EXISTS face_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    face_width FLOAT NOT NULL,
                    eye_distance FLOAT NOT NULL,
                    cheek_area FLOAT NOT NULL,
                    nose_height FLOAT NOT NULL,
                    temple_position FLOAT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                )
            """,
            "frames": """
                CREATE TABLE IF NOT EXISTS frames (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name VARCHAR(255) NOT NULL,
                    brand VARCHAR(255) NOT NULL,
                    price INTEGER NOT NULL,
                    style VARCHAR(50) NOT NULL,
                    shape VARCHAR(50) NOT NULL,
                    material VARCHAR(50) NOT NULL,
                    color VARCHAR(50) NOT NULL,
                    frame_width FLOAT NOT NULL,
                    lens_width FLOAT NOT NULL,
                    bridge_width FLOAT NOT NULL,
                    temple_length FLOAT NOT NULL,
                    lens_height FLOAT NOT NULL,
                    weight FLOAT NOT NULL,
                    recommended_face_width_min FLOAT,
                    recommended_face_width_max FLOAT,
                    recommended_nose_height_min FLOAT,
                    recommended_nose_height_max FLOAT,
                    personal_color_season VARCHAR(50),
                    face_shape_types TEXT,
                    style_tags TEXT,
                    image_urls TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """
        }
        
        # テーブル作成実行
        created_tables = []
        for table_name, table_sql in tables.items():
            try:
                if table_name not in existing_tables:
                    cursor.execute(table_sql)
                    created_tables.append(table_name)
            except Exception as e:
                logger.error(f"テーブル '{table_name}' 作成エラー: {str(e)}")
        
        # テストユーザーの作成（users テーブルが空の場合）
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.info("テストユーザーを作成します")
            cursor.execute("""
                INSERT INTO users (email, gender, birth_date)
                VALUES ('test@example.com', 'other', '2000-01-01')
            """)
        
        # コミットして接続を閉じる
        conn.commit()
        conn.close()
        
        if created_tables:
            logger.info(f"以下のテーブルを作成しました: {', '.join(created_tables)}")
        else:
            logger.info("新たに作成が必要なテーブルはありませんでした")
        
        return True
    except Exception as e:
        logger.error(f"SQLiteテーブル作成エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # Azureデプロイ時に実行される場合のエントリーポイント
    logger.info("Azureデプロイ設定スクリプトを実行しています...")
    success = initialize_database()
    
    if success:
        logger.info("デプロイ設定が正常に完了しました")
        sys.exit(0)
    else:
        logger.error("デプロイ設定中にエラーが発生しました")
        sys.exit(1) 