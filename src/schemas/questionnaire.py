from pydantic import BaseModel
from typing import List
from datetime import datetime

class UserResponseBase(BaseModel):
    question_id: int
    selected_preference_ids: List[int]

class UserResponseCreate(UserResponseBase):
    pass

class UserResponse(UserResponseBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class QuestionnaireSubmission(BaseModel):
    responses: List[UserResponseBase] 