from fastapi import FastAPI, Depends, HTTPException, Request, BackgroundTasks, Response, Body
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from .database import engine, Base, get_db, check_mysql_connection, get_db_path
from sqlalchemy.orm import Session
from .routers import frame, questionnaire
import logging
import traceback
import os
import sys
from .routers import recommendation, ai_explanation
from sqlalchemy.sql import text
import sqlite3
from pathlib import Path
import time
import json
import importlib
import uuid
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import inspect

# 全モデルを明示的にインポート
from .models.user import User, StyleQuestion, Preference, UserResponse, FaceMeasurement
from .models.frame import Frame

# ロギングの設定
logging.basicConfig(
    level=logging.getLevelName(os.environ.get("LOG_LEVEL", "INFO")),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)

# 初期化情報をログに出力
logger.info(f"Pythonバージョン: {sys.version}")
logger.info(f"現在の作業ディレクトリ: {os.getcwd()}")
logger.info(f"環境変数: DB_HOST={os.environ.get('DB_HOST', 'なし')}")
logger.info(f"環境変数: STORAGE_PATH={os.environ.get('STORAGE_PATH', 'なし')}")
logger.info(f"環境変数: SQLITE_PATH={os.environ.get('SQLITE_PATH', 'なし')}")
logger.info(f"環境変数: APPLY_MIGRATIONS={os.environ.get('APPLY_MIGRATIONS', 'なし')}")
logger.info(f"環境変数: SQLITE_FALLBACK={os.environ.get('SQLITE_FALLBACK', 'なし')}")

# クラッシュした場合のエラーログを収集
def log_exception(exctype, value, tb):
    logger.exception("未処理の例外: {0}".format(value))
    logger.exception(traceback.format_exception(exctype, value, tb))

sys.excepthook = log_exception

app = FastAPI(
    title="EyeSmile API",
    description="API for EyeSmile application",
    version="1.0.0"
)

# CORSミドルウェア設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 開発環境では全てのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],  # すべてのHTTPメソッドを許可
    allow_headers=["*"],  # すべてのHTTPヘッダーを許可
    expose_headers=["*"]
)

# デプロイ環境の検出
is_azure = os.getenv('WEBSITE_SITE_NAME') is not None
logger.info(f"実行環境: {'Azure' if is_azure else 'ローカル'}")

# Azureの場合、環境変数に基づいてマイグレーションを実行
if is_azure:
    apply_migrations = os.getenv('APPLY_MIGRATIONS', '').lower() == 'true'
    if apply_migrations:
        try:
            logger.info("Azure環境 - APPLY_MIGRATIONS=true が設定されています。データベースマイグレーションを実行します...")
            # SQLiteではなくAzure MySQLに対してテーブル作成を実行
            Base.metadata.create_all(bind=engine)
            logger.info("Azure環境 - データベーステーブルを正常に作成しました")
            
            # SQLiteにフォールバックしているか確認
            if str(engine.url).startswith('sqlite'):
                logger.info("SQLiteフォールバックを検出しました。すべてのテーブルが存在するか確認します。")
                with engine.connect() as conn:
                    # 主要なテーブルの存在をチェック
                    tables = ['users', 'user_responses', 'face_measurements', 'frames', 'style_questions', 'preferences']
                    missing_tables = []
                    for table in tables:
                        try:
                            result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                            if not result.fetchone():
                                missing_tables.append(table)
                        except Exception as table_e:
                            logger.error(f"テーブル確認エラー: {str(table_e)}")
                    
                    if missing_tables:
                        logger.warning(f"次のテーブルが見つかりません: {', '.join(missing_tables)}。再作成を試みます。")
                        # 明示的に全テーブルを作成 (SQLiteの場合IF NOT EXISTSが適用される)
                        Base.metadata.create_all(bind=engine)
                        logger.info("SQLiteテーブルの再作成が完了しました")
        except Exception as e:
            logger.error(f"Azure環境 - データベースマイグレーションエラー: {str(e)}")
            logger.error(traceback.format_exc())
            # エラーをログに記録するだけで、起動は続行
            logger.warning("データベースエラーが発生しましたが、アプリケーションは起動を続行します")
    else:
        logger.info("Azure環境を検出 - APPLY_MIGRATIONS=true が設定されていないため、データベース初期化をスキップします")
else:
    try:
        # ローカル環境でのみテーブル作成を実行
        logger.info("ローカル環境 - データベーステーブルを作成しています...")
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブルを正常に作成しました")

        # SQLiteにフォールバックした場合にテーブルが存在するか確認
        if str(engine.url).startswith('sqlite'):
            logger.info("SQLite環境を検出 - テーブルの存在を確認します")
            with engine.connect() as conn:
                # 主要なテーブルの存在をチェック
                tables = ['users', 'user_responses', 'face_measurements', 'frames', 'style_questions', 'preferences']
                missing_tables = []
                for table in tables:
                    try:
                        result = conn.execute(text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table}'"))
                        if not result.fetchone():
                            missing_tables.append(table)
                    except Exception as table_e:
                        logger.error(f"テーブル確認エラー: {str(table_e)}")
                
                if missing_tables:
                    logger.warning(f"次のテーブルが見つかりません: {', '.join(missing_tables)}。再作成を試みます。")
                    # 明示的に全テーブルを作成 (SQLiteの場合IF NOT EXISTSが適用される)
                    Base.metadata.create_all(bind=engine)
                    logger.info("SQLiteテーブルの再作成が完了しました")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        logger.error(traceback.format_exc())
        # エラーをログに記録するだけで、起動は続行
        logger.warning("データベースエラーが発生しましたが、アプリケーションは起動を続行します")

# CORS問題を解決するためのグローバルミドルウェア
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        
        # 許可されたオリジンを環境変数から取得
        allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
        origin = request.headers.get("Origin", "")
        
        # リクエスト元のオリジンが許可リストにあるか、「*」が設定されている場合
        if "*" in allowed_origins or origin in allowed_origins:
            # 具体的なオリジンを設定（安全性向上のため）
            response.headers["Access-Control-Allow-Origin"] = origin if origin else "*"
            response.headers["Access-Control-Allow-Credentials"] = "true"
            response.headers["Access-Control-Allow-Methods"] = "GET, POST, PUT, DELETE, OPTIONS"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
            response.headers["Access-Control-Max-Age"] = "3600"
        
        # リクエストパスをログに記録
        logger.info(f"リクエスト処理完了: {request.method} {request.url.path}")
        return response
    except Exception as e:
        logger.error(f"ミドルウェアエラー: {str(e)}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error"}
        )

# OPTIONSリクエストに対するプレフライトハンドラー
@app.options("/{path:path}")
async def options_handler(request: Request, path: str):
    logger.info(f"OPTIONSリクエスト受信: {path}")
    
    # 許可されたオリジンを環境変数から取得
    allowed_origins = os.getenv("ALLOWED_ORIGINS", "*").split(",")
    origin = request.headers.get("Origin", "")
    
    # リクエスト元のオリジンが許可リストにあるか、「*」が設定されている場合
    if "*" in allowed_origins or origin in allowed_origins:
        return JSONResponse(
            content={},
            headers={
                "Access-Control-Allow-Origin": origin if origin else "*",
                "Access-Control-Allow-Credentials": "true",
                "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
                "Access-Control-Max-Age": "3600",
            },
        )
    else:
        return JSONResponse(content={}, status_code=204)

# 特定エンドポイント用のプレフライトハンドラー
@app.options("/api/v1/questionnaire/submit")
async def options_questionnaire_submit():
    logger.info("アンケート送信エンドポイントへのOPTIONSリクエスト受信")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        },
    )

@app.options("/api/v1/questionnaire/face-measurements/submit")
async def options_face_measurements_submit():
    logger.info("顔測定データ送信エンドポイントへのOPTIONSリクエスト受信")
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "POST, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization",
            "Access-Control-Max-Age": "3600",
        },
    )

# 起動確認用の軽量なエンドポイント
@app.get("/")
async def root():
    return {"status": "ok", "message": "EyeSmile API is running"}

# ヘルスチェックエンドポイント - データベース接続なし
@app.get("/api/health")
async def api_health():
    return {"status": "healthy", "database": "not checked"}

# ヘルスチェックエンドポイント - データベース接続あり
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # データベース接続をテスト
        logger.info("データベース接続テスト実行中...")
        db.execute("SELECT 1")
        logger.info("データベース接続テスト成功")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"データベース接続エラー: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

# 顔測定データ用のエンドポイント
@app.post("/api/v1/face-measurements/submit")
async def face_measurements_endpoint(
    measurements: dict,
    db: Session = Depends(get_db)
):
    try:
        logger.info(f"顔測定データを受信: {measurements}")
        # データ処理は実際のアプリケーションロジックに合わせて実装
        return {"status": "success", "data": measurements}
    except Exception as e:
        logger.error(f"顔測定データ処理エラー: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 静的ファイル用のディレクトリを準備
static_dir = os.getenv("STORAGE_PATH", "static/images")
os.makedirs(static_dir, exist_ok=True)
logger.info(f"静的ファイルディレクトリを準備: {static_dir}")

# 静的ファイルを提供する設定
try:
    app.mount("/static", StaticFiles(directory="static"), name="static")
    logger.info("静的ファイルのマウントに成功しました")
except Exception as e:
    logger.error(f"静的ファイルのマウントに失敗: {str(e)}")

# Azure App Serviceが8000ポートを使用する設定
PORT = int(os.getenv("PORT", os.getenv("WEBSITES_PORT", 8000)))
HOST = os.getenv("HOST", "0.0.0.0")

# ルーターの登録
app.include_router(frame.router)
app.include_router(questionnaire.router)
app.include_router(recommendation.router)
app.include_router(ai_explanation.router)

# 起動時のログ
logger.info("アプリケーションが正常に起動しました")

# アプリケーションを直接実行する場合
if __name__ == "__main__":
    import uvicorn
    logger.info(f"サーバーを起動: {HOST}:{PORT}")
    uvicorn.run("src.main:app", host=HOST, port=PORT, reload=True)

# SQLiteテーブル存在確認関数
def check_sqlite_tables():
    """SQLiteデータベースに必要なテーブルが存在するか確認し、存在しない場合は作成を試みる"""
    db_path = get_db_path()
    logger.info(f"SQLiteテーブル確認を開始: {db_path}")
    
    if not os.path.exists(db_path):
        logger.warning(f"SQLiteデータベースファイルが存在しません: {db_path}")
        try:
            # ファイルの作成を試みる
            Path(db_path).touch()
            logger.info(f"SQLiteデータベースファイルを作成しました: {db_path}")
            os.chmod(db_path, 0o666)  # 読み書き権限を設定
        except Exception as e:
            logger.error(f"SQLiteデータベースファイル作成エラー: {str(e)}")
            return False
    
    try:
        # データベース接続
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 必要なテーブル名のリスト
        required_tables = [
            "users", "style_questions", "preferences",
            "user_responses", "face_measurements", "frames"
        ]
        
        # 現在のテーブル一覧を取得
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        existing_tables = [row[0] for row in cursor.fetchall()]
        logger.info(f"既存のSQLiteテーブル: {existing_tables}")
        
        # 不足しているテーブルを特定
        missing_tables = [table for table in required_tables if table not in existing_tables]
        
        if missing_tables:
            logger.warning(f"不足しているテーブル: {missing_tables}")
            # モデルからテーブルを作成
            try:
                from .models.base import Base
                logger.info("SQLAlchemyモデルからテーブルを作成します")
                Base.metadata.create_all(bind=engine)
                logger.info("テーブル作成が完了しました")
                
                # 作成後に再確認
                cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
                updated_tables = [row[0] for row in cursor.fetchall()]
                logger.info(f"テーブル作成後のテーブル一覧: {updated_tables}")
                
                # それでも不足しているテーブルがある場合はSQL文で作成を試みる
                still_missing = [table for table in required_tables if table not in updated_tables]
                if still_missing:
                    logger.warning(f"まだ不足しているテーブル: {still_missing}")
                    # SQL文での作成を実行
                    create_tables_with_sql(conn, cursor, still_missing)
            except Exception as e:
                logger.error(f"テーブル作成エラー: {str(e)}")
                logger.error(traceback.format_exc())
                return False
        else:
            logger.info("すべての必要なテーブルが存在します")
        
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"SQLiteテーブル確認エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# SQL文でテーブルを作成する関数
def create_tables_with_sql(conn, cursor, missing_tables):
    """SQL文を使用して不足しているテーブルを作成する"""
    logger.info("SQL文でテーブルを作成します")
    
    sql_statements = {
        "users": """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE,
                hashed_password TEXT,
                is_active BOOLEAN DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """,
        "style_questions": """
            CREATE TABLE IF NOT EXISTS style_questions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                question_text TEXT NOT NULL,
                options TEXT NOT NULL,
                category TEXT NOT NULL,
                order_index INTEGER
            );
        """,
        "preferences": """
            CREATE TABLE IF NOT EXISTS preferences (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                preference_data TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            );
        """,
        "user_responses": """
            CREATE TABLE IF NOT EXISTS user_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_id INTEGER,
                response TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id),
                FOREIGN KEY (question_id) REFERENCES style_questions (id)
            );
        """,
        "face_measurements": """
            CREATE TABLE IF NOT EXISTS face_measurements (
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
        """,
        "frames": """
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
        """
    }
    
    for table in missing_tables:
        if table in sql_statements:
            try:
                logger.info(f"{table}テーブルをSQL文で作成します")
                cursor.execute(sql_statements[table])
                logger.info(f"{table}テーブル作成完了")
            except Exception as e:
                logger.error(f"{table}テーブル作成エラー: {str(e)}")
        else:
            logger.warning(f"{table}テーブルのSQL文が定義されていません")
    
    conn.commit()

# アプリケーション起動時の処理
@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時の処理"""
    logger.info("アプリケーション起動処理を開始します")
    
    # データベースマイグレーション（必要に応じて）
    if os.getenv("RUN_MIGRATIONS", "false").lower() == "true":
        logger.info("データベースマイグレーションを実行します")
        # マイグレーション処理をここに追加
    else:
        logger.info("データベースマイグレーションはスキップされます")
    
    # テストデータの追加（開発環境のみ）
    if os.getenv("ENV", "development") == "development":
        try:
            from sqlalchemy.orm import Session
            from .database import SessionLocal
            from . import crud, schemas
            from .models.frame import Frame as ModelsFrame  # 修正：Frameモデルを正しくインポート
            
            db = SessionLocal()
            
            # 既存のフレーム数を確認
            frame_count = db.query(ModelsFrame).count()  # 修正：ModelsFrameを使用
            logger.info(f"現在のフレーム数: {frame_count}")
            
            # フレームが少ない場合はテストデータを追加
            if frame_count < 5:
                logger.info("テストデータを追加します")
                
                # テストフレームデータ
                test_frames = [
                    schemas.FrameCreate(
                        name="クラシックラウンド",
                        brand="Zoff",
                        price=15000,
                        style="クラシック",
                        shape="ラウンド",
                        material="チタン",
                        color="ブラウン",
                        frame_width=135.0,
                        lens_width=45.0,
                        bridge_width=20.0,
                        temple_length=145.0,
                        lens_height=45.0,
                        weight=20.0,
                        recommended_face_width_min=120.0,
                        recommended_face_width_max=140.0,
                        recommended_nose_height_min=70.0,
                        recommended_nose_height_max=90.0,
                        personal_color_season="Winter",
                        face_shape_types=["楕円", "丸型"],
                        style_tags=["クラシック", "ビジネス"],
                        image_urls=["/images/frames/zoff-sporty-round.jpg"]
                    ),
                    schemas.FrameCreate(
                        name="スクエアフレーム",
                        brand="JINS",
                        price=12000,
                        style="モダン",
                        shape="スクエア",
                        material="プラスチック",
                        color="ブラック",
                        frame_width=140.0,
                        lens_width=48.0,
                        bridge_width=19.0,
                        temple_length=145.0,
                        lens_height=42.0,
                        weight=18.0,
                        recommended_face_width_min=115.0,
                        recommended_face_width_max=135.0,
                        recommended_nose_height_min=65.0,
                        recommended_nose_height_max=85.0,
                        personal_color_season="Winter",
                        face_shape_types=["楕円", "ハート型"],
                        style_tags=["モダン", "カジュアル"],
                        image_urls=["/images/frames/jins-square.jpg"]
                    ),
                    schemas.FrameCreate(
                        name="ボストンタイプ",
                        brand="Eyewear Shop",
                        price=18000,
                        style="レトロ",
                        shape="ボストン",
                        material="セルロース",
                        color="アンバー",
                        frame_width=138.0,
                        lens_width=47.0,
                        bridge_width=21.0,
                        temple_length=147.0,
                        lens_height=43.0,
                        weight=22.0,
                        recommended_face_width_min=122.0,
                        recommended_face_width_max=142.0,
                        recommended_nose_height_min=72.0,
                        recommended_nose_height_max=92.0,
                        personal_color_season="Autumn",
                        face_shape_types=["四角", "ダイヤモンド"],
                        style_tags=["レトロ", "ファッション"],
                        image_urls=["/images/frames/eyewear-boston.jpg"]
                    ),
                    schemas.FrameCreate(
                        name="オーバルメタル",
                        brand="RayBan",
                        price=22000,
                        style="クラシック",
                        shape="オーバル",
                        material="メタル",
                        color="ゴールド",
                        frame_width=132.0,
                        lens_width=44.0,
                        bridge_width=18.0,
                        temple_length=140.0,
                        lens_height=40.0,
                        weight=15.0,
                        recommended_face_width_min=118.0,
                        recommended_face_width_max=138.0,
                        recommended_nose_height_min=68.0,
                        recommended_nose_height_max=88.0,
                        personal_color_season="Spring",
                        face_shape_types=["四角", "長方形"],
                        style_tags=["ヴィンテージ", "エレガント"],
                        image_urls=["/images/frames/rayban-oval.jpg"]
                    ),
                    schemas.FrameCreate(
                        name="キャットアイ",
                        brand="Prada",
                        price=30000,
                        style="ファッション",
                        shape="キャットアイ",
                        material="アセテート",
                        color="レッド",
                        frame_width=136.0,
                        lens_width=46.0,
                        bridge_width=19.0,
                        temple_length=143.0,
                        lens_height=46.0,
                        weight=23.0,
                        recommended_face_width_min=116.0,
                        recommended_face_width_max=136.0,
                        recommended_nose_height_min=66.0,
                        recommended_nose_height_max=86.0,
                        personal_color_season="Winter",
                        face_shape_types=["ハート型", "楕円"],
                        style_tags=["ファッション", "トレンド"],
                        image_urls=["/images/frames/prada-cateye.jpg"]
                    )
                ]
                
                # フレームを追加
                for frame_data in test_frames:
                    try:
                        crud.frame.create_frame(db, frame_data)
                        logger.info(f"フレームを追加しました: {frame_data.brand} {frame_data.name}")
                    except Exception as e:
                        logger.error(f"フレーム追加エラー: {e}", exc_info=True)
                
                logger.info("テストデータの追加が完了しました")
            
            db.close()
            
        except Exception as e:
            logger.error(f"テストデータ追加エラー: {e}", exc_info=True)
    
    logger.info("アプリケーション起動処理が完了しました")
