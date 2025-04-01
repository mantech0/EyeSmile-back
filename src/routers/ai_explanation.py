from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session
import logging
from ..database import get_db
from .. import crud, schemas
from ..services.ai_service import generate_glasses_explanation
from typing import Dict, Any

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/ai-explanation",
    tags=["ai_explanation"]
)

@router.post("/generate")
async def generate_explanation(
    request_data: Dict[str, Any],
    db: Session = Depends(get_db),
    response: Response = None
):
    """メガネフレームに関する説明をAIで生成します"""
    # CORSヘッダーを追加
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "3600"
    
    try:
        logger.info("AIによる説明生成リクエストを受信しました")
        
        # リクエストデータの検証
        frame_data = request_data.get("frame_data")
        face_data = request_data.get("face_data")
        style_preference = request_data.get("style_preference")
        
        if not frame_data or not face_data:
            raise HTTPException(
                status_code=400,
                detail="フレームデータと顔データが必要です"
            )
        
        # AI説明を生成
        explanation = await generate_glasses_explanation(
            frame_data=frame_data,
            face_data=face_data,
            style_preference=style_preference
        )
        
        return {
            "status": "success",
            "explanation": explanation
        }
        
    except Exception as e:
        logger.error(f"説明生成中にエラーが発生しました: {str(e)}", exc_info=True)
        # エラーが発生した場合でも何らかのレスポンスを返す
        return {
            "status": "error",
            "message": f"説明の生成中にエラーが発生しました: {str(e)}",
            "explanation": {
                "fit_explanation": "フレームサイズがあなたの顔に合っています。",
                "style_explanation": "このフレームのスタイルはあなたの好みに合っています。",
                "feature_highlights": [
                    "フィット感のチェック",
                    "長時間着用での快適さ",
                    "スタイルとの相性",
                    "レンズ品質の確認",
                    "フレーム調整の余地"
                ]
            }
        }

@router.options("/generate")
async def options_generate():
    """CORS Preflight Requestへの対応"""
    return {
        "Allow": "POST, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With"
    } 