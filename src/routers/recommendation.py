from fastapi import APIRouter, Depends, HTTPException, Body
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import models, schemas, crud
from ..services.frame_recommendation import FrameRecommendationService
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/recommendations",
    tags=["recommendations"]
)

# 推薦リクエストのスキーマ
class RecommendationRequest(schemas.BaseModel):
    face_data: schemas.FaceMeasurement
    style_preference: Optional[schemas.StylePreference] = None

# 顔データに基づいてメガネフレームを推薦するエンドポイント
@router.post("/glasses", response_model=schemas.RecommendationResponse)
def recommend_glasses(
    request: RecommendationRequest = Body(...),
    db: Session = Depends(get_db)
):
    """顔の測定データとスタイル好みに基づいてメガネフレームを推薦します"""
    try:
        logger.info(f"メガネフレーム推薦リクエスト受信: {request}")
        
        # 顔測定データを取得
        face_data = request.face_data
        style_preference = request.style_preference

        # データベースからフレームを取得
        frames = crud.frame.get_recommended_frames(
            db=db,
            face_width=face_data.face_width,
            nose_height=face_data.nose_height,
            personal_color=style_preference.personal_color if style_preference else None,
            style_preferences=style_preference.preferred_styles if style_preference else [],
            limit=10
        )
        
        if not frames:
            # フレームがない場合は全てのフレームから選択
            logger.warning("条件に合うフレームが見つからないため、全てのフレームから選択します")
            frames = crud.frame.get_frames(db=db, limit=10)
            
        if not frames:
            raise HTTPException(status_code=404, detail="推薦可能なフレームが見つかりませんでした")
            
        # ユーザーの好みのデータを作成（スタイル設定から）
        user_preferences = []
        if style_preference:
            # スタイル好みからユーザー設定を構築
            for style in style_preference.preferred_styles:
                user_preferences.append(models.UserResponse(
                    preference=models.Preference(
                        preference_type="style",
                        preference_value=style
                    ),
                    response_value=1  # 好き
                ))
            
            for shape in style_preference.preferred_shapes:
                user_preferences.append(models.UserResponse(
                    preference=models.Preference(
                        preference_type="shape",
                        preference_value=shape
                    ),
                    response_value=1  # 好き
                ))
                
            for material in style_preference.preferred_materials:
                user_preferences.append(models.UserResponse(
                    preference=models.Preference(
                        preference_type="material",
                        preference_value=material
                    ),
                    response_value=1  # 好き
                ))
        
        # サービスを使用してフレームをランク付け
        ranked_frames = []
        face_measurement = models.FaceMeasurement(
            face_width=face_data.face_width,
            eye_distance=face_data.eye_distance,
            cheek_area=face_data.cheek_area,
            nose_height=face_data.nose_height,
            temple_position=face_data.temple_position
        )
        
        for frame in frames:
            recommendation = FrameRecommendationService.calculate_total_score(
                frame=frame,
                face_measurement=face_measurement,
                user_preferences=user_preferences
            )
            ranked_frames.append(recommendation)
        
        # スコアで降順ソート
        ranked_frames.sort(key=lambda x: x.total_score, reverse=True)
        
        # 最もスコアの高いフレームを主要推薦として選択
        primary_recommendation = ranked_frames[0] if ranked_frames else None
        
        # 残りのフレームを代替推薦として選択
        alternative_recommendations = ranked_frames[1:5] if len(ranked_frames) > 1 else []
        
        # 顔の形状を決定
        face_shape = "楕円型"  # デフォルト値
        if face_data.face_width > 140:
            face_shape = "丸型"
        elif face_data.face_width < 130:
            face_shape = "細長型"
            
        # スタイルカテゴリを決定
        style_category = style_preference.preferred_styles[0] if style_preference and style_preference.preferred_styles else "クラシック"
        
        # フィット説明を生成
        fit_explanation = f"あなたの顔幅({face_data.face_width}mm)と鼻の高さ({face_data.nose_height}mm)に適したフレームを選びました。"
        
        # スタイル説明を生成
        style_explanation = "お好みのスタイルに合わせたデザインを選びました。"
        if style_preference and style_preference.preferred_styles:
            style_tags = ", ".join(style_preference.preferred_styles)
            style_explanation = f"あなたの好みの{style_tags}スタイルに合ったデザインを選びました。"
        
        # 特徴ハイライトを生成
        feature_highlights = [
            f"{primary_recommendation.frame.material}素材",
            f"{primary_recommendation.frame.shape}シェイプ",
            f"{primary_recommendation.frame.color}カラー"
        ]
        
        # レスポンスを作成
        response = schemas.RecommendationResponse(
            primary_recommendation=primary_recommendation,
            alternative_recommendations=alternative_recommendations,
            face_analysis=schemas.FaceAnalysis(
                face_shape=face_shape,
                style_category=style_category,
                demo_mode=False
            ),
            recommendation_details=schemas.RecommendationDetails(
                fit_explanation=fit_explanation,
                style_explanation=style_explanation,
                feature_highlights=feature_highlights
            )
        )
        
        logger.info(f"メガネフレーム推薦レスポンス生成完了: 主要推薦={response.primary_recommendation.frame.name}, "
                   f"代替推薦数={len(response.alternative_recommendations)}")
        
        return response
        
    except Exception as e:
        logger.error(f"メガネフレーム推薦処理エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推薦の処理中にエラーが発生しました: {str(e)}") 