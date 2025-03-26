from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import engine, Base, get_db
from sqlalchemy.orm import Session
from .routers import frame, questionnaire
import logging
import traceback
import os

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="EyeSmile API",
    description="API for EyeSmile application",
    version="1.0.0"
)

# CORSミドルウェア設定（main.pyのインポート後、ルーター登録前に設定）
origins = [
    "http://localhost:3000",
    "http://localhost:5173",
    "https://eyesmile-frontend.vercel.app",
    "https://tech0-gen-8-step4-eyesmile.azurewebsites.net",
    "https://tech0-gen-8-step4-eyesmile-back.azurewebsites.net",
    "https://tech0-gen-8-step4-eyesmile-front.azurestaticapps.net",
    "*"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# データベース初期化
# Azure環境では最初は軽量な処理にして、タイムアウトを回避
is_azure = os.getenv('WEBSITE_SITE_NAME') is not None
try:
    if not is_azure:
        # ローカル環境では完全なテーブル作成を実行
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブルを正常に作成しました")
    else:
        # Azure環境では軽量な接続テストのみ実行
        logger.info("Azure環境を検出しました - データベース初期化をスキップします")
        # ヘルスチェックエンドポイントでテーブル作成を実行します
except Exception as e:
    logger.error(f"データベース初期化エラー: {e}")
    logger.error(traceback.format_exc())
    # エラーをログに記録するだけで、起動は続行 (raise しない)
    logger.warning("データベースエラーが発生しましたが、アプリケーションは起動を続行します")

# CORS問題を解決するためのグローバルミドルウェア
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
        response.headers["Access-Control-Max-Age"] = "3600"
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
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "3600",
        },
    )

# ヘルスチェックエンドポイント
@app.get("/health")
async def health_check(db: Session = Depends(get_db)):
    try:
        # データベース接続をテスト
        db.execute("SELECT 1")
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        logger.error(f"Database connection error: {e}")
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
        logger.error(f"顔測定データ処理エラー: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# ルーターの登録
app.include_router(frame.router)
app.include_router(questionnaire.router)
