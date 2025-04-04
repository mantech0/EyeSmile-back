from .questionnaire import UserResponse, UserResponseBase, UserResponseCreate, QuestionnaireSubmission
from .face_measurement import FaceMeasurement, FaceMeasurementBase, FaceMeasurementCreate
from .frame import Frame, FrameBase, FrameCreate, FrameRecommendationResponse
from .recommendation import StylePreference, FaceAnalysis, RecommendationDetails, RecommendationResponse
from pydantic import BaseModel
from typing import List, Optional

# AI説明用のスキーマ
class FaceData(BaseModel):
    face_width: float
    eye_distance: float
    cheek_area: float
    nose_height: float
    temple_position: float

class StyleData(BaseModel):
    personal_color: Optional[str] = None
    preferred_styles: List[str] = []
    preferred_shapes: List[str] = []
    preferred_materials: List[str] = []
    preferred_colors: List[str] = []

__all__ = [
    'UserResponse', 'UserResponseBase', 'UserResponseCreate', 'QuestionnaireSubmission',
    'FaceMeasurement', 'FaceMeasurementBase', 'FaceMeasurementCreate',
    'Frame', 'FrameBase', 'FrameCreate', 'FrameRecommendationResponse',
    'StylePreference', 'FaceAnalysis', 'RecommendationDetails', 'RecommendationResponse',
    'FaceData', 'StyleData'
] 