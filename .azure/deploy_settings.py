#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Azureデプロイ用の設定スクリプト - シンプル版
最小限のデータベース初期化とサンプルデータのロードを行います
"""

import os
import sys
import logging
import sqlite3
import json
import traceback
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger("deploy_settings")

# パスの設定
def main():
    """メイン処理"""
    try:
        logger.info("シンプル版デプロイ設定スクリプトを実行します")
        
        # 作業ディレクトリの確認
        current_dir = os.getcwd()
        logger.info(f"現在の作業ディレクトリ: {current_dir}")
        
        # SQLiteファイルのパス
        db_path = os.path.join(current_dir, "test.db")
        logger.info(f"SQLiteデータベースパス: {db_path}")
        
        # SQLiteファイルの存在確認
        if os.path.exists(db_path):
            logger.info(f"SQLiteデータベースファイルが存在します: {db_path}")
            try:
                # 権限設定
                os.chmod(db_path, 0o666)
                logger.info("SQLiteファイルの権限を設定しました")
            except Exception as e:
                logger.warning(f"権限設定エラー: {str(e)}")
        else:
            logger.info("SQLiteデータベースファイルが存在しません。新規作成します")
            try:
                # 空ファイル作成
                Path(db_path).touch()
                os.chmod(db_path, 0o666)
                logger.info("SQLiteファイルを作成しました")
            except Exception as e:
                logger.error(f"ファイル作成エラー: {str(e)}")
                return False
        
        # 最小限のテーブル作成
        create_minimal_tables(db_path)
        
        # 成功
        logger.info("デプロイ設定が完了しました")
        return True
        
    except Exception as e:
        logger.error(f"予期せぬエラーが発生しました: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def create_minimal_tables(db_path):
    """最小限のテーブルを作成"""
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 最小限のテーブル作成
        create_tables_sql = """
        -- ユーザーテーブル
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT,
            hashed_password TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- フレームテーブル
        CREATE TABLE IF NOT EXISTS frames (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            description TEXT,
            image_path TEXT,
            style TEXT,
            material TEXT,
            color TEXT,
            shape TEXT,
            frame_width REAL,
            frame_height REAL,
            bridge_width REAL,
            temple_length REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        
        -- 顔測定データテーブル
        CREATE TABLE IF NOT EXISTS face_measurements (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            face_width REAL,
            face_height REAL,
            temple_width REAL,
            bridge_width REAL,
            pupillary_distance REAL,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
        
        # テーブル作成実行
        cursor.executescript(create_tables_sql)
        logger.info("基本テーブルを作成しました")
        
        # テーブル確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        logger.info(f"作成されたテーブル: {[t[0] for t in tables]}")
        
        # ユーザーデータの登録（存在しない場合）
        cursor.execute("SELECT COUNT(*) FROM users")
        if cursor.fetchone()[0] == 0:
            cursor.execute(
                "INSERT INTO users (email, hashed_password) VALUES (?, ?)",
                ("demo@example.com", "demopassword")
            )
            logger.info("デモユーザーを登録しました")
        
        # フレームサンプルデータ登録（存在しない場合）
        cursor.execute("SELECT COUNT(*) FROM frames")
        if cursor.fetchone()[0] == 0:
            sample_frames = [
                {
                    "name": "クラシックオーバル",
                    "description": "オーバル型の上品なデザイン",
                    "image_path": "frames/classic_oval.jpg",
                    "style": "クラシック",
                    "material": "チタン",
                    "color": "ゴールド",
                    "shape": "オーバル",
                    "frame_width": 140.0,
                    "frame_height": 45.0,
                    "bridge_width": 20.0,
                    "temple_length": 145.0
                },
                {
                    "name": "モダンスクエア",
                    "description": "四角型のモダンなデザイン",
                    "image_path": "frames/modern_square.jpg",
                    "style": "モダン",
                    "material": "プラスチック",
                    "color": "黒",
                    "shape": "スクエア",
                    "frame_width": 142.0,
                    "frame_height": 48.0,
                    "bridge_width": 19.0,
                    "temple_length": 148.0
                }
            ]
            
            for frame in sample_frames:
                cursor.execute(
                    """
                    INSERT INTO frames (
                        name, description, image_path, style, material, color, shape,
                        frame_width, frame_height, bridge_width, temple_length
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        frame["name"], frame["description"], frame["image_path"],
                        frame["style"], frame["material"], frame["color"], frame["shape"],
                        frame["frame_width"], frame["frame_height"], frame["bridge_width"], frame["temple_length"]
                    )
                )
            logger.info(f"{len(sample_frames)}件のサンプルフレームを登録しました")
        
        # コミット
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        logger.error(f"テーブル作成エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # メイン処理の実行
    if main():
        logger.info("処理が成功しました")
        sys.exit(0)
    else:
        logger.error("処理が失敗しました")
        sys.exit(1) 