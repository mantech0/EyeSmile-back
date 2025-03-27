from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import engine, Base, get_db
from sqlalchemy.orm import Session
from .routers import frame, questionnaire, recommendation
import logging
import traceback
import os
import sys

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
    allow_origins=["*"],  # すべてのオリジンを許可
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# デプロイ環境の検出
is_azure = os.getenv('WEBSITE_SITE_NAME') is not None
logger.info(f"実行環境: {'Azure' if is_azure else 'ローカル'}")

# Azureの場合、データベース初期化は完全にスキップ
if not is_azure:
    try:
        # ローカル環境でのみテーブル作成を実行
        logger.info("データベーステーブルを作成しています...")
        Base.metadata.create_all(bind=engine)
        logger.info("データベーステーブルを正常に作成しました")
    except Exception as e:
        logger.error(f"データベース初期化エラー: {str(e)}")
        logger.error(traceback.format_exc())
        # エラーをログに記録するだけで、起動は続行
        logger.warning("データベースエラーが発生しましたが、アプリケーションは起動を続行します")
else:
    logger.info("Azure環境を検出 - データベース初期化をスキップします")

# CORS問題を解決するためのグローバルミドルウェア
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    try:
        response = await call_next(request)
        # すべてのリクエストに対してCORSヘッダーを追加
        response.headers["Access-Control-Allow-Origin"] = "*"
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
    return JSONResponse(
        content={},
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "3600",
        },
    )

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

# ルーターの登録
app.include_router(frame.router)
app.include_router(questionnaire.router)
app.include_router(recommendation.router)

# 起動時のログ
logger.info("アプリケーションが正常に起動しました")
