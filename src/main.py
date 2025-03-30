from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.ext.declarative import declarative_base
from . import crud, models, schemas
from .database import engine, get_db ,Base
from typing import List
import logging
from pydantic import BaseModel, EmailStr #追加 
import mysql.connector #追加
from datetime import datetime #追加
from .models.user import User
from src.models import user  # 追加
from src.schemas import questionnaire
import traceback #追加

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting EyeSmile API server...")

app = FastAPI(
    title="EyeSmile API",
    description="API for EyeSmile application",
    version="1.0.0"
)

# Create database tables dbunitに移行

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

# 会員情報の登録
# Pydanticモデル（受け取るデータ形式）
class RegisterRequest(BaseModel):
    email: EmailStr
    gender: str
    birth_date: str  # 例: "1994-09-28"

# 会員情報の登録
@app.post("/api/register")
def register_user(data: RegisterRequest, db: Session = Depends(get_db)):
    try:
        now = datetime.now()
        new_user = User(
            email=data.email,
            gender=data.gender,
            birth_date=data.birth_date,
            created_at=now,
            updated_at=now
        )
        db.add(new_user)
        db.commit()
        db.refresh(new_user)  # 登録したユーザー情報を返す場合
        return {"message": "登録が完了しました", "user_id": new_user.id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# ログイン機能
class LoginRequest(BaseModel):
    email: EmailStr
    birth_date: str  # 生年月日を仮パスワード代わりに使う例

@app.post("/api/login")
def login_user(data: LoginRequest, db: Session = Depends(get_db)):
    try:
        user = db.query(User).filter(User.email == data.email).first()
        if not user:
            raise HTTPException(status_code=404, detail="ユーザーが見つかりません")

        # 仮にbirth_dateをパスワード代わりに使う簡易認証（要調整）
        if str(user.birth_date) != data.birth_date:
            raise HTTPException(status_code=401, detail="認証に失敗しました")

        return {
            "message": "ログイン成功",
            "email": user.email  # ← user_id から email に変更
        }
    except Exception as e:
        logger.error(f"Login error: {e}")
        logger.error(traceback.format_exc())  # ← スタックトレースをログ出力
        raise HTTPException(status_code=500, detail="ログイン処理でエラーが発生しました")


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
@app.post("/api/v1/questionnaire/submit", response_model=List[questionnaire.UserResponse])
async def submit_questionnaire(
    submission: questionnaire.QuestionnaireSubmission,
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
@app.get("/api/v1/questionnaire/responses", response_model=List[questionnaire.UserResponse])
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