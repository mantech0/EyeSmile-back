from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from .database import engine, Base
from .routers import frame
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

# Create database tables
try:
    Base.metadata.create_all(bind=engine)
    logger.info("Database tables created successfully")
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    logger.error(traceback.format_exc())
    raise

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tech0-gen-8-step4-eyesmile.azurewebsites.net",
        "https://tech0-gen-8-step4-eyesmile-back.azurewebsites.net",
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173"
    ],
    allow_credentials=True,
    allow_methods=["*"],  # すべてのメソッドを許可
    allow_headers=["*"],  # すべてのヘッダーを許可
)

# ルーターの登録
app.include_router(frame.router)
