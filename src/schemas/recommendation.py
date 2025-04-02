from pydantic import BaseModel
from typing import List, Optional
from .frame import FrameRecommendationResponse
from .face_measurement import FaceMeasurement

class StylePreference(BaseModel):
    """ユーザーのスタイル好み設定"""
    personal_color: Optional[str] = None
    preferred_styles: List[str] = []
    preferred_shapes: List[str] = []
    preferred_materials: List[str] = []
    preferred_colors: List[str] = []

class FaceAnalysis(BaseModel):
    """顔分析の結果"""
    face_shape: str
    style_category: str
    demo_mode: bool = False

class RecommendationDetails(BaseModel):
    """推薦詳細情報"""
    fit_explanation: str
    style_explanation: str
    feature_highlights: List[str] = []

class RecommendationResponse(BaseModel):
    """フレーム推薦のレスポンス"""
    primary_recommendation: FrameRecommendationResponse
    alternative_recommendations: List[FrameRecommendationResponse] = []
    face_analysis: FaceAnalysis
    recommendation_details: RecommendationDetails 