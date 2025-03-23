from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from . import crud, models, schemas
from .database import engine, get_db, Base
from typing import List
import logging
import traceback
from datetime import datetime

# ロギングの設定
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Starting EyeSmile API server...")

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
        "http://127.0.0.1:5173",
        "http://localhost:8080"
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS", "HEAD"],
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
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/")
async def root():
    return {"message": "Welcome to EyeSmile API"}

# テストデータの作成
@app.post("/api/v1/test-data/create")
async def create_test_data(db: Session = Depends(get_db)):
    try:
        # 質問データの作成
        questions = [
            models.StyleQuestion(
                id=1,
                question_type="scene",
                question_text="どんなシーンでアイウェアを着用をしたいですか？",
                display_order=1,
                options=["仕事", "日常生活", "遊び", "スポーツ", "その他"],
                multiple_select=True
            ),
            models.StyleQuestion(
                id=2,
                question_type="image",
                question_text="どのような印象に見られたいですか？",
                display_order=2,
                options=["知的", "活発", "落ち着き", "若々しく", "クール", "おしゃれ", "かっこよく", "かわいく", "その他"],
                multiple_select=True
            ),
            models.StyleQuestion(
                id=3,
                question_type="fashion",
                question_text="どんな服装を普段しますか？",
                display_order=3,
                options=["カジュアル", "フォーマル", "スポーティ", "モード", "シンプル", "ストリート", "アウトドア", "その他"],
                multiple_select=True
            ),
            models.StyleQuestion(
                id=4,
                question_type="personal_color",
                question_text="パーソナルカラーは何色ですか？",
                display_order=4,
                options=["Spring（スプリング）", "Summer（サマー）", "Autumn（オータム）", "Winter（ウィンター）", "わからない"],
                multiple_select=False
            )
        ]

        # プリファレンスデータの作成
        preferences = [
            # シーン
            models.Preference(id=1, category="scene", preference_value="work", display_name="仕事"),
            models.Preference(id=2, category="scene", preference_value="daily", display_name="日常生活"),
            models.Preference(id=3, category="scene", preference_value="play", display_name="遊び"),
            models.Preference(id=4, category="scene", preference_value="sports", display_name="スポーツ"),
            models.Preference(id=5, category="scene", preference_value="other", display_name="その他"),

            # イメージ
            models.Preference(id=11, category="image", preference_value="intellectual", display_name="知的"),
            models.Preference(id=12, category="image", preference_value="active", display_name="活発"),
            models.Preference(id=13, category="image", preference_value="calm", display_name="落ち着き"),
            models.Preference(id=14, category="image", preference_value="young", display_name="若々しく"),
            models.Preference(id=15, category="image", preference_value="cool", display_name="クール"),
            models.Preference(id=16, category="image", preference_value="fashionable", display_name="おしゃれ"),
            models.Preference(id=17, category="image", preference_value="stylish", display_name="かっこよく"),
            models.Preference(id=18, category="image", preference_value="cute", display_name="かわいく"),
            models.Preference(id=19, category="image", preference_value="other", display_name="その他"),

            # ファッション
            models.Preference(id=20, category="fashion", preference_value="casual", display_name="カジュアル"),
            models.Preference(id=21, category="fashion", preference_value="formal", display_name="フォーマル"),
            models.Preference(id=22, category="fashion", preference_value="sporty", display_name="スポーティ"),
            models.Preference(id=23, category="fashion", preference_value="mode", display_name="モード"),
            models.Preference(id=24, category="fashion", preference_value="simple", display_name="シンプル"),
            models.Preference(id=25, category="fashion", preference_value="street", display_name="ストリート"),
            models.Preference(id=26, category="fashion", preference_value="outdoor", display_name="アウトドア"),
            models.Preference(id=27, category="fashion", preference_value="other", display_name="その他"),

            # パーソナルカラー
            models.Preference(id=28, category="personal_color", preference_value="spring", display_name="Spring（スプリング）"),
            models.Preference(id=29, category="personal_color", preference_value="summer", display_name="Summer（サマー）"),
            models.Preference(id=30, category="personal_color", preference_value="autumn", display_name="Autumn（オータム）"),
            models.Preference(id=31, category="personal_color", preference_value="winter", display_name="Winter（ウィンター）"),
            models.Preference(id=32, category="personal_color", preference_value="unknown", display_name="わからない")
        ]

        # データベースに保存
        db.add_all(questions)
        db.add_all(preferences)
        db.commit()

        return {"message": "Test data created successfully"}
    except Exception as e:
        logger.error(f"Failed to create test data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# テストユーザーの作成
@app.post("/api/v1/users/create-test")
async def create_test_user(db: Session = Depends(get_db)):
    try:
        # テストユーザーの存在確認
        user = db.query(models.User).filter(models.User.id == 1).first()
        if user:
            return {"message": "Test user already exists", "user_id": user.id}

        # テストユーザーの作成
        test_user = models.User(
            id=1,
            email="test@example.com",
            gender="other",
            birth_date=datetime.now().date()
        )
        db.add(test_user)
        db.commit()
        db.refresh(test_user)
        return {"message": "Test user created successfully", "user_id": test_user.id}
    except Exception as e:
        logger.error(f"Failed to create test user: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

# 新しいエンドポイント：回答の保存
@app.post("/api/v1/questionnaire/submit")
async def submit_questionnaire(
    submission: schemas.QuestionnaireSubmission,
    db: Session = Depends(get_db)
):
    logger.info(f"Received submission: {submission}")
    temporary_user_id = 1
    
    try:
        # ユーザーの存在確認
        user = db.query(models.User).filter(models.User.id == temporary_user_id).first()
        if not user:
            logger.error(f"User not found: {temporary_user_id}")
            raise HTTPException(status_code=404, detail=f"User {temporary_user_id} not found")

        # 回答の保存前にデータの検証
        for response in submission.responses:
            question = db.query(models.StyleQuestion).filter(models.StyleQuestion.id == response.question_id).first()
            if not question:
                logger.error(f"Question not found: {response.question_id}")
                raise HTTPException(status_code=404, detail=f"Question {response.question_id} not found")
            
            for pref_id in response.selected_preference_ids:
                preference = db.query(models.Preference).filter(models.Preference.id == pref_id).first()
                if not preference:
                    logger.error(f"Preference not found: {pref_id}")
                    raise HTTPException(status_code=404, detail=f"Preference {pref_id} not found")

        responses = crud.questionnaire.create_user_responses(
            db=db,
            user_id=temporary_user_id,
            responses=submission.responses
        )
        logger.info(f"Successfully saved responses: {responses}")
        return {"status": "success", "message": "回答が保存されました"}
    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Failed to save responses: {str(e)}")
        logger.error(f"Error type: {type(e)}")
        logger.error(f"Error details: {e.__dict__}")
        logger.error(traceback.format_exc())
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

# 顔の測定データの保存
@app.post("/api/v1/face-measurements/submit", response_model=schemas.FaceMeasurement)
async def submit_face_measurement(
    face_measurement: schemas.FaceMeasurementCreate,
    db: Session = Depends(get_db)
):
    logger.info(f"Received face measurement: {face_measurement}")
    try:
        # ユーザーの存在確認
        user = db.query(models.User).filter(models.User.id == face_measurement.user_id).first()
        if not user:
            logger.error(f"User not found: {face_measurement.user_id}")
            raise HTTPException(status_code=404, detail=f"User {face_measurement.user_id} not found")

        measurement = crud.face_measurement.create_face_measurement(
            db=db,
            face_measurement=face_measurement
        )
        logger.info(f"Successfully saved face measurement: {measurement}")
        return measurement
    except HTTPException as he:
        logger.error(f"HTTP Exception: {he.detail}")
        raise
    except Exception as e:
        logger.error(f"Failed to save face measurement: {str(e)}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500,
            detail=f"Failed to save face measurement: {str(e)}"
        )

# 顔の測定データの取得
@app.get("/api/v1/face-measurements/{user_id}", response_model=List[schemas.FaceMeasurement])
async def get_face_measurements(
    user_id: int,
    db: Session = Depends(get_db)
):
    measurements = crud.face_measurement.get_face_measurements(db=db, user_id=user_id)
    if not measurements:
        raise HTTPException(status_code=404, detail=f"No face measurements found for user {user_id}")
    return measurements

# 最新の顔の測定データの取得
@app.get("/api/v1/face-measurements/{user_id}/latest", response_model=schemas.FaceMeasurement)
async def get_latest_face_measurement(
    user_id: int,
    db: Session = Depends(get_db)
):
    measurement = crud.face_measurement.get_latest_face_measurement(db=db, user_id=user_id)
    if not measurement:
        raise HTTPException(status_code=404, detail=f"No face measurements found for user {user_id}")
    return measurement 