from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import engine, get_db
from typing import List
import logging

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
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    raise

# CORSの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://tech0-gen-8-step4-eyesmile.azurewebsites.net",
        "http://localhost:3000",
        "*"  # 開発中は一時的に全てのオリジンを許可
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

@app.get("/api/v1/health")
async def health_check():
    try:
        # データベース接続テスト
        db = next(get_db())
        db.execute("SELECT 1")
        return {"status": "healthy", "service": "EyeSmile API"}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to EyeSmile API"}

# 新しいエンドポイント：回答の保存
@app.post("/api/v1/questionnaire/submit", response_model=List[schemas.UserResponse])
async def submit_questionnaire(
    submission: schemas.QuestionnaireSubmission,
    db: Session = Depends(get_db)
):
    logger.info(f"Received submission: {submission}")
    temporary_user_id = 1
    
    try:
        responses = crud.questionnaire.create_user_responses(
            db=db,
            user_id=temporary_user_id,
            responses=submission.responses
        )
        logger.info(f"Successfully saved responses: {responses}")
        return responses
    except Exception as e:
        logger.error(f"Failed to save responses: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save responses: {str(e)}"
        )

# 回答の取得
@app.get("/api/v1/questionnaire/responses", response_model=List[schemas.UserResponse])
async def get_questionnaire_responses(
    db: Session = Depends(get_db)
):
    # 仮のユーザーID（本来はログインユーザーのIDを使用）
    temporary_user_id = 1
    
    responses = crud.questionnaire.get_user_responses(
        db=db,
        user_id=temporary_user_id
    )
    return responses 