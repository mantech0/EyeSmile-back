from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from .. import crud, schemas

router = APIRouter(
    prefix="/api/v1/questionnaire",
    tags=["questionnaire"]
)

@router.post("/submit", response_model=List[schemas.UserResponse])
def submit_questionnaire(
    responses: schemas.QuestionnaireSubmission,
    db: Session = Depends(get_db)
):
    """アンケートの回答を送信します"""
    try:
        # 仮のユーザーID（本来はログインユーザーのIDを使用）
        temporary_user_id = 1
        
        # 回答を保存
        db_responses = crud.questionnaire.create_user_responses(
            db=db,
            user_id=temporary_user_id,
            responses=responses.responses
        )
        return db_responses
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"回答の保存中にエラーが発生しました: {str(e)}"
        ) 