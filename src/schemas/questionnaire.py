from pydantic import BaseModel
from typing import List
from datetime import datetime

class UserResponseBase(BaseModel):
    question_id: int
    selected_preference_ids: List[int]

class UserResponseCreate(UserResponseBase):
    pass

class UserResponse(BaseModel):
    id: int
    user_id: int
    question_id: int
    selected_preference_id: int
    created_at: datetime
    updated_at: datetime = None

    class Config:
        from_attributes = True

class QuestionnaireSubmission(BaseModel):
    responses: List[UserResponseBase] 