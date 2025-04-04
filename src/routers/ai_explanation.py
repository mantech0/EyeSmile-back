from fastapi import APIRouter, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional, Union
import logging
from .. import schemas

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ai",
    tags=["ai"]
)

class FrameData(BaseModel):
    id: int
    name: str
    brand: str
    price: int
    style: str
    shape: str
    material: str
    color: str
    
# 共通のFaceDataとStyleDataクラスを利用    
class ExplanationRequest(BaseModel):
    frame: FrameData
    face_data: schemas.FaceData
    style_preference: Optional[schemas.StyleData] = None

class ExplanationResponse(BaseModel):
    status: str
    explanation: Dict[str, Union[str, List[str]]]

@router.post("/generate-explanation", response_model=ExplanationResponse)
def generate_explanation(request: ExplanationRequest = Body(...)):
    """フレームと顔データに基づいた説明をAIで生成します"""
    try:
        logger.info(f"説明生成リクエスト受信: フレーム={request.frame.name}")
        
        # ここでは実際のAI処理はなく、テンプレート化した説明を生成
        frame = request.frame
        face_data = request.face_data
        style = request.style_preference
        
        # フィット説明を生成
        fit_explanation = f"{frame.brand}の{frame.name}は、あなたの顔幅({face_data.face_width:.1f}mm)と鼻の高さ({face_data.nose_height:.1f}mm)に適したサイズです。"
        
        if frame.shape.lower() == "round" or frame.shape.lower() == "ラウンド":
            fit_explanation += " 丸みを帯びたフレームはあなたの顔の特徴を和らげ、柔らかい印象を与えます。"
        elif frame.shape.lower() == "square" or frame.shape.lower() == "スクエア":
            fit_explanation += " シャープなフレームはあなたの顔に知的で洗練された印象を加えます。"
        else:
            fit_explanation += f" {frame.shape}シェイプはあなたの顔立ちに調和します。"
        
        # スタイル説明を生成
        style_explanation = f"{frame.style}スタイルの{frame.material}素材フレームは、"
        
        preferred_styles = []
        if style and style.preferred_styles:
            preferred_styles = style.preferred_styles
            
        if preferred_styles:
            style_explanation += f"あなたが好む{', '.join(preferred_styles)}テイストに合致し、"
            
        if frame.style.lower() == "classic" or frame.style.lower() == "クラシック":
            style_explanation += "時代を超えた上品さを提供します。"
        elif frame.style.lower() == "modern" or frame.style.lower() == "モダン":
            style_explanation += "洗練された現代的な印象を与えます。"
        elif frame.style.lower() == "casual" or frame.style.lower() == "カジュアル":
            style_explanation += "自然でリラックスした日常使いに最適です。"
        else:
            style_explanation += "あなたの個性を引き立てます。"
        
        # 特徴ハイライトを生成
        feature_highlights = [
            f"{frame.material}素材（軽量で耐久性があります）",
            f"{frame.shape}シェイプ（あなたの顔型に適しています）",
            f"{frame.color}カラー（あなたの肌色・髪色に調和します）"
        ]
        
        response = {
            "status": "success",
            "explanation": {
                "fit_explanation": fit_explanation,
                "style_explanation": style_explanation,
                "feature_highlights": feature_highlights
            }
        }
        
        logger.info(f"説明生成完了: {response}")
        return response
        
    except Exception as e:
        logger.error(f"説明生成処理エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"説明の生成中にエラーが発生しました: {str(e)}")
