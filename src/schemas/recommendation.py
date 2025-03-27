from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from .frame import Frame, FrameRecommendationResponse

class FaceData(BaseModel):
    """顔の測定データ"""
    face_width: float
    eye_distance: float
    cheek_area: float
    nose_height: float
    temple_position: float
    
class StylePreference(BaseModel):
    """スタイル設定"""
    personal_color: Optional[str] = None  # Spring, Summer, Autumn, Winter
    preferred_styles: List[str] = []      # カジュアル、フォーマル、スポーティー等
    preferred_shapes: List[str] = []      # ラウンド、スクエア、オーバル等
    preferred_materials: List[str] = []   # プラスチック、メタル等
    preferred_colors: List[str] = []      # ブラック、ブラウン、クリア等
    
class RecommendationRequest(BaseModel):
    """メガネ推薦リクエスト"""
    face_data: FaceData
    style_preference: Optional[StylePreference] = None
    
class RecommendationDetail(BaseModel):
    """推薦理由の詳細"""
    fit_explanation: str  # フィットの説明 (例: "顔幅と鼻の高さに最適です")
    style_explanation: str  # スタイルの説明 (例: "あなたの好みのカジュアルスタイルに合います")
    feature_highlights: List[str]  # 特筆すべき特徴 (例: ["軽量設計", "耐久性フレーム"])
    
class RecommendationResponse(BaseModel):
    """メガネ推薦レスポンス"""
    primary_recommendation: FrameRecommendationResponse
    alternative_recommendations: List[FrameRecommendationResponse]
    face_analysis: dict  # 顔分析結果 (例: {"face_shape": "楕円形", "style_category": "クール"})
    recommendation_details: RecommendationDetail 