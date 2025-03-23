from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

class FrameBase(BaseModel):
    name: str
    brand: str
    price: int
    style: str
    shape: str
    material: str
    color: str
    
    # サイズ情報
    frame_width: float
    lens_width: float
    bridge_width: float
    temple_length: float
    lens_height: float
    weight: float

    # 推奨情報
    recommended_face_width_min: Optional[float] = None
    recommended_face_width_max: Optional[float] = None
    recommended_nose_height_min: Optional[float] = None
    recommended_nose_height_max: Optional[float] = None
    
    # スタイル情報
    personal_color_season: Optional[str] = None
    face_shape_types: List[str] = []
    style_tags: List[str] = []
    
    # 画像情報
    image_urls: List[str] = []

class FrameCreate(FrameBase):
    pass

class Frame(FrameBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class FrameRecommendationResponse(BaseModel):
    frame: Frame
    fit_score: float
    style_score: float
    total_score: float
    recommendation_reason: str 