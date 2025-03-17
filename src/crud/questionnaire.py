from sqlalchemy.orm import Session
from typing import List
from .. import models, schemas

def create_user_responses(
    db: Session,
    user_id: int,
    responses: List[schemas.UserResponseBase]
) -> List[models.UserResponse]:
    db_responses = []
    
    for response in responses:
        # 各選択肢に対してレコードを作成
        for preference_id in response.selected_preference_ids:
            db_response = models.UserResponse(
                user_id=user_id,
                question_id=response.question_id,
                selected_preference_id=preference_id
            )
            db_responses.append(db_response)
    
    db.add_all(db_responses)
    db.commit()
    for response in db_responses:
        db.refresh(response)
    
    return db_responses

def get_user_responses(
    db: Session,
    user_id: int
) -> List[models.UserResponse]:
    return db.query(models.UserResponse).filter(
        models.UserResponse.user_id == user_id
    ).all() 