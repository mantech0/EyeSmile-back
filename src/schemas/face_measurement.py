from pydantic import BaseModel
from datetime import datetime

class FaceMeasurementBase(BaseModel):
    face_width: float      # 顔の幅
    eye_distance: float    # 目の間の距離
    cheek_area: float      # 頬の面積
    nose_height: float     # 鼻の高さ
    temple_position: float # こめかみの位置

class FaceMeasurementCreate(FaceMeasurementBase):
    user_id: int

class FaceMeasurement(FaceMeasurementBase):
    id: int
    user_id: int
    created_at: datetime

    class Config:
        from_attributes = True 