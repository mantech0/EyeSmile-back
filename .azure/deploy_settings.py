#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Azureデプロイ用の設定スクリプト
データベース初期化とサンプルデータのロードを行います
"""

import os
import sys
import logging
import sqlite3
import json
import time
import traceback
from datetime import datetime
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("deploy_settings")

# アプリケーションルートディレクトリの設定
APP_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(APP_ROOT)

def initialize_database():
    """SQLiteデータベースの初期化"""
    logger.info("データベース初期化を開始します")
    
    # 現在の作業ディレクトリを設定
    os.chdir(APP_ROOT)
    logger.info(f"作業ディレクトリ: {os.getcwd()}")
    
    # 環境変数のチェック
    sqlite_path = os.environ.get("SQLITE_PATH", "test.db")
    if not os.path.isabs(sqlite_path):
        sqlite_path = os.path.join(os.getcwd(), sqlite_path)
    logger.info(f"SQLiteデータベースパス: {sqlite_path}")
    
    # データベースファイルの確認
    db_exists = os.path.exists(sqlite_path)
    if db_exists:
        logger.info(f"既存のSQLiteデータベースが見つかりました: {sqlite_path}")
        try:
            # ファイル権限の設定
            os.chmod(sqlite_path, 0o666)
            logger.info("データベースファイルの権限を設定しました")
        except Exception as e:
            logger.warning(f"データベースファイル権限設定エラー: {str(e)}")
    else:
        logger.info("SQLiteデータベースファイルが見つかりません。新規作成します")
        try:
            # データベースディレクトリの確認
            db_dir = os.path.dirname(sqlite_path)
            if db_dir and not os.path.exists(db_dir):
                os.makedirs(db_dir, exist_ok=True)
                logger.info(f"データベースディレクトリを作成しました: {db_dir}")
            
            # 空のデータベースファイルを作成
            with open(sqlite_path, 'w') as f:
                pass
            os.chmod(sqlite_path, 0o666)
            logger.info(f"新しいSQLiteデータベースファイルを作成しました: {sqlite_path}")
        except Exception as e:
            logger.error(f"データベースファイル作成エラー: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    
    # テーブルの作成
    if create_sqlite_tables(sqlite_path):
        # サンプルデータの登録
        load_sample_data(sqlite_path)
        return True
    return False

def create_sqlite_tables(db_path):
    """必要なテーブルをSQLiteデータベースに作成"""
    logger.info("SQLiteテーブルの作成を開始します")
    
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テーブル存在確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"既存のテーブル: {existing_tables}")
        
        # usersテーブル
        if "users" not in existing_tables:
            logger.info("usersテーブルを作成します")
            cursor.execute("""
                CREATE TABLE users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    email TEXT UNIQUE,
                    hashed_password TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                );
            """)
        
        # style_questionsテーブル
        if "style_questions" not in existing_tables:
            logger.info("style_questionsテーブルを作成します")
            cursor.execute("""
                CREATE TABLE style_questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_text TEXT NOT NULL,
                    options TEXT NOT NULL,
                    category TEXT NOT NULL,
                    order_index INTEGER
                );
            """)
        
        # preferencesテーブル
        if "preferences" not in existing_tables:
            logger.info("preferencesテーブルを作成します")
            cursor.execute("""
                CREATE TABLE preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    preference_data TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
            """)
        
        # user_responsesテーブル
        if "user_responses" not in existing_tables:
            logger.info("user_responsesテーブルを作成します")
            cursor.execute("""
                CREATE TABLE user_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    question_id INTEGER,
                    response TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id),
                    FOREIGN KEY (question_id) REFERENCES style_questions (id)
                );
            """)
        
        # face_measurementsテーブル
        if "face_measurements" not in existing_tables:
            logger.info("face_measurementsテーブルを作成します")
            cursor.execute("""
                CREATE TABLE face_measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    face_width REAL,
                    face_height REAL,
                    pupillary_distance REAL,
                    temple_width REAL,
                    bridge_width REAL,
                    image_path TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users (id)
                );
            """)
        
        # framesテーブル
        if "frames" not in existing_tables:
            logger.info("framesテーブルを作成します")
            cursor.execute("""
                CREATE TABLE frames (
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
            """)
        
        # コミットして接続を閉じる
        conn.commit()
        
        # テーブル作成後の確認
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        updated_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"テーブル作成後のテーブル一覧: {updated_tables}")
        
        conn.close()
        logger.info("全てのテーブルが正常に作成されました")
        return True
    
    except Exception as e:
        logger.error(f"テーブル作成エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def load_sample_data(db_path):
    """サンプルデータをデータベースに登録"""
    logger.info("サンプルデータの登録を開始します")
    
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # テストユーザーの作成（存在しない場合）
        cursor.execute("SELECT COUNT(*) FROM users;")
        user_count = cursor.fetchone()[0]
        
        if user_count == 0:
            logger.info("テストユーザーを作成します")
            # パスワードはハッシュ化されていることを想定（実際の実装に合わせる）
            test_password = "testpassword"  # 本番環境では適切なハッシュ化が必要
            cursor.execute(
                "INSERT INTO users (email, hashed_password, is_active) VALUES (?, ?, ?);",
                ("test@example.com", test_password, 1)
            )
            logger.info("テストユーザーを作成しました")
        
        # スタイルに関する質問の登録（存在しない場合）
        cursor.execute("SELECT COUNT(*) FROM style_questions;")
        question_count = cursor.fetchone()[0]
        
        if question_count == 0:
            logger.info("スタイル質問を登録します")
            style_questions = [
                {
                    "question_text": "普段どのようなメガネのスタイルが好きですか？",
                    "options": json.dumps(["クラシック", "モダン", "スポーティ", "ファッショナブル"]),
                    "category": "style",
                    "order_index": 1
                },
                {
                    "question_text": "顔の形はどのような形ですか？",
                    "options": json.dumps(["丸型", "卵型", "四角型", "ハート型", "ダイヤモンド型"]),
                    "category": "face_shape",
                    "order_index": 2
                },
                {
                    "question_text": "どのような色のフレームが好みですか？",
                    "options": json.dumps(["黒", "茶色", "ゴールド", "シルバー", "カラフル"]),
                    "category": "color",
                    "order_index": 3
                }
            ]
            
            for question in style_questions:
                cursor.execute(
                    "INSERT INTO style_questions (question_text, options, category, order_index) VALUES (?, ?, ?, ?);",
                    (question["question_text"], question["options"], question["category"], question["order_index"])
                )
            
            logger.info(f"{len(style_questions)}件のスタイル質問を登録しました")
        
        # フレームデータの登録（存在しない場合）
        cursor.execute("SELECT COUNT(*) FROM frames;")
        frame_count = cursor.fetchone()[0]
        
        if frame_count == 0:
            logger.info("サンプルフレームデータを登録します")
            sample_frames = [
                {
                    "name": "クラシックオーバル",
                    "description": "オーバル型の上品なデザイン",
                    "image_path": "frames/classic_oval.jpg",
                    "frame_width": 140.0,
                    "frame_height": 45.0,
                    "bridge_width": 20.0,
                    "temple_length": 145.0,
                    "style": "クラシック",
                    "material": "チタン",
                    "color": "ゴールド",
                    "shape": "オーバル"
                },
                {
                    "name": "モダンスクエア",
                    "description": "四角型のモダンなデザイン",
                    "image_path": "frames/modern_square.jpg",
                    "frame_width": 142.0,
                    "frame_height": 48.0,
                    "bridge_width": 19.0,
                    "temple_length": 148.0,
                    "style": "モダン",
                    "material": "プラスチック",
                    "color": "黒",
                    "shape": "スクエア"
                },
                {
                    "name": "ラウンドメタル",
                    "description": "丸型のメタルフレーム",
                    "image_path": "frames/round_metal.jpg",
                    "frame_width": 138.0,
                    "frame_height": 44.0,
                    "bridge_width": 21.0,
                    "temple_length": 145.0,
                    "style": "クラシック",
                    "material": "メタル",
                    "color": "シルバー",
                    "shape": "ラウンド"
                },
                {
                    "name": "キャットアイ",
                    "description": "キャットアイ型のおしゃれなフレーム",
                    "image_path": "frames/cat_eye.jpg",
                    "frame_width": 140.0,
                    "frame_height": 46.0,
                    "bridge_width": 20.0,
                    "temple_length": 147.0,
                    "style": "ファッショナブル",
                    "material": "アセテート",
                    "color": "茶色",
                    "shape": "キャットアイ"
                },
                {
                    "name": "スポーティレクタングル",
                    "description": "スポーツ向けの長方形フレーム",
                    "image_path": "frames/sporty_rectangle.jpg",
                    "frame_width": 144.0,
                    "frame_height": 42.0,
                    "bridge_width": 18.0,
                    "temple_length": 150.0,
                    "style": "スポーティ",
                    "material": "プラスチック",
                    "color": "黒",
                    "shape": "レクタングル"
                }
            ]
            
            for frame in sample_frames:
                cursor.execute(
                    """
                    INSERT INTO frames (
                        name, description, image_path, 
                        frame_width, frame_height, bridge_width, temple_length,
                        style, material, color, shape
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """,
                    (
                        frame["name"], frame["description"], frame["image_path"],
                        frame["frame_width"], frame["frame_height"], frame["bridge_width"], frame["temple_length"],
                        frame["style"], frame["material"], frame["color"], frame["shape"]
                    )
                )
            
            logger.info(f"{len(sample_frames)}件のサンプルフレームを登録しました")
        
        # コミットして接続を閉じる
        conn.commit()
        conn.close()
        logger.info("サンプルデータの登録が完了しました")
        return True
    
    except Exception as e:
        logger.error(f"サンプルデータ登録エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    # データベースの初期化
    if initialize_database():
        logger.info("データベース初期化が正常に完了しました")
        sys.exit(0)
    else:
        logger.error("データベース初期化に失敗しました")
        sys.exit(1) 