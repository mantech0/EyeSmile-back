from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from .database import engine, Base, get_db
from sqlalchemy.orm import Session
from .routers import frame, questionnaire
import logging
import traceback

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

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    logger.error(traceback.format_exc())
    raise

# CORS問題を解決するためのグローバルミドルウェア
@app.middleware("http")
async def add_cors_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["Access-Control-Allow-Origin"] = "*"
    response.headers["Access-Control-Allow-Methods"] = "*"
    response.headers["Access-Control-Allow-Headers"] = "*"
    response.headers["Access-Control-Max-Age"] = "3600"
    return response

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
