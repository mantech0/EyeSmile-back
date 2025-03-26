from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
from typing import List, Dict, Any
import logging
from ..database import get_db
from .. import crud, schemas

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/questionnaire",
    tags=["questionnaire"]
)

@router.post("/submit")
def submit_questionnaire(
    responses: schemas.QuestionnaireSubmission,
    db: Session = Depends(get_db),
    response: Response = None
):
    """アンケートの回答を送信します"""
    # CORSヘッダーを追加
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        logger.info(f"受信したデータ: {responses}")
        # 仮のユーザーID（本来はログインユーザーのIDを使用）
        temporary_user_id = 1
        
        # 回答を保存
        db_responses = crud.questionnaire.create_user_responses(
            db=db,
            user_id=temporary_user_id,
            responses=responses.responses
        )
        
        # 簡易なレスポンスを返す
        return {"status": "success", "message": "回答が正常に保存されました"}
    except Exception as e:
        logger.error(f"エラーの詳細: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"回答の保存中にエラーが発生しました: {str(e)}"
        )

# 顔測定用のエンドポイントを追加
@router.post("/face-measurements/submit", response_model=schemas.FaceMeasurement)
def submit_face_measurements(
    measurements: schemas.FaceMeasurementCreate,
    db: Session = Depends(get_db),
    response: Response = None
):
    """顔の測定データを送信します"""
    # CORSヘッダーを追加
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "*"
        response.headers["Access-Control-Allow-Headers"] = "*"
    
    try:
        logger.info(f"受信した顔測定データ: {measurements}")
        # 仮のユーザーID（本来はログインユーザーのIDを使用）
        temporary_user_id = 1

        # 顔測定データを保存
        # 本来はcrudモジュールの関数を呼び出すが、簡易実装として成功レスポンスを返す
        return {
            "id": 1,
            "user_id": temporary_user_id,
            "face_width": measurements.face_width,
            "eye_distance": measurements.eye_distance,
            "cheek_area": measurements.cheek_area,
            "nose_height": measurements.nose_height,
            "temple_position": measurements.temple_position,
            "created_at": "2023-01-01T00:00:00"
        }
    except Exception as e:
        logger.error(f"エラーの詳細: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"顔測定データの保存中にエラーが発生しました: {str(e)}"
        ) 