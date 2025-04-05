"""
Azureデプロイ用の設定と初期化スクリプト
"""

import os
import sys
import traceback
import logging
import sqlite3
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def initialize_database():
    """
    SQLiteデータベースを初期化して必要なテーブルを作成します
    """
    try:
        # データベースファイルのパス
        db_path = 'test.db'
        
        # テーブル作成用のSQL
        create_tables_sql = """
        -- ユーザーテーブル
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email VARCHAR(255) NOT NULL UNIQUE,
            gender VARCHAR(10) NOT NULL,
            birth_date DATE NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- 質問テーブル
        CREATE TABLE IF NOT EXISTS style_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            question_type VARCHAR(50) NOT NULL,
            question_text VARCHAR(500) NOT NULL,
            display_order INTEGER NOT NULL,
            options JSON,
            multiple_select BOOLEAN DEFAULT 0
        );

        -- 好みテーブル
        CREATE TABLE IF NOT EXISTS preferences (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category VARCHAR(50) NOT NULL,
            preference_value VARCHAR(100) NOT NULL,
            display_name VARCHAR(255) NOT NULL,
            description VARCHAR(1000),
            color_code VARCHAR(7)
        );

        -- ユーザー回答テーブル
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
        );

        -- 顔測定テーブル
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
        );

        -- フレームテーブル
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(255) NOT NULL,
            brand VARCHAR(255) NOT NULL,
            price INTEGER NOT NULL,
            style VARCHAR(50),
            shape VARCHAR(50),
            material VARCHAR(50),
            color VARCHAR(50),
            frame_width FLOAT,
            lens_width FLOAT,
            bridge_width FLOAT,
            temple_length FLOAT,
            lens_height FLOAT,
            weight FLOAT,
            recommended_face_width_min FLOAT,
            recommended_face_width_max FLOAT,
            recommended_nose_height_min FLOAT,
            recommended_nose_height_max FLOAT,
            personal_color_season VARCHAR(50),
            face_shape_types JSON,
            style_tags JSON,
            image_urls JSON,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        logger.info("SQLiteデータベース初期化を開始します...")
        
        # データベース接続とテーブル作成
        with sqlite3.connect(db_path) as conn:
            conn.executescript(create_tables_sql)
            logger.info("テーブルが正常に作成されました")
            
            # フレームテーブルにデータがあるか確認
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM frames")
            count = cursor.fetchone()[0]
            
            if count == 0:
                logger.info("フレームデータが存在しません。ダミーデータを生成します...")
                # ダミーデータ生成スクリプトを実行
                try:
                    from dummy_data_generator import main as generate_dummy_data
                    generate_dummy_data()
                    logger.info("ダミーデータの生成が完了しました")
                except Exception as e:
                    logger.error(f"ダミーデータ生成エラー: {str(e)}")
            else:
                logger.info(f"既存のフレームデータが {count} 件見つかりました")
        
        return True
    
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
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