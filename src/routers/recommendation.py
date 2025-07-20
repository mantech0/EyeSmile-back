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
        
        # 残りのフレームを代替推薦として選択（最大4つ）
        alternative_recommendations = ranked_frames[1:5] if len(ranked_frames) > 1 else []
        
        # リストフィールドのNoneを空リストに置き換え
        if primary_recommendation and primary_recommendation.frame:
            if primary_recommendation.frame.face_shape_types is None:
                primary_recommendation.frame.face_shape_types = []
            if primary_recommendation.frame.style_tags is None:
                primary_recommendation.frame.style_tags = []
            if primary_recommendation.frame.image_urls is None:
                primary_recommendation.frame.image_urls = []
                
        for rec in alternative_recommendations:
            if rec.frame:
                if rec.frame.face_shape_types is None:
                    rec.frame.face_shape_types = []
                if rec.frame.style_tags is None:
                    rec.frame.style_tags = []
                if rec.frame.image_urls is None:
                    rec.frame.image_urls = []
        
        # フレーム説明用の変数を取得
        face_shape = "ラウンド"
        if face_data.face_width > 140:
            face_shape = "丸型"
        elif face_data.face_width < 130:
            face_shape = "細長型"
            
        # レンズ幅の表示用テキスト
        lens_width_display = "50mm"
        try:
            # primary_recommendationからレンズ幅を取得
            if primary_recommendation and primary_recommendation.frame:
                if primary_recommendation.frame.lens_width:
                    lens_width_display = f"{primary_recommendation.frame.lens_width}mm"
                elif primary_recommendation.frame.lens_height:
                    lens_width_display = f"{primary_recommendation.frame.lens_height}mm"
        except Exception as e:
            logger.error(f"レンズ幅取得エラー: {e}")
            
        # フレーム形状
        frame_shape = "ラウンド"
        if primary_recommendation and primary_recommendation.frame:
            frame_shape = primary_recommendation.frame.lens_shape_name or "ラウンド"
        
        # フィット説明を生成
        fit_explanation = f"{frame_shape}型のフレームはあなたの顔幅({face_data.face_width:.1f}mm)に適しています。レンズ幅{lens_width_display}のサイズ感が、顔全体のバランスを整えます。ブリッジ幅20mmが鼻に自然にフィットし、長時間の着用でも快適です。"
        
        # スタイル説明を生成
        style_explanation = "お好みのスタイルに合わせたデザインを選びました。"
        if style_preference and style_preference.preferred_styles and primary_recommendation and primary_recommendation.frame:
            brand_name = primary_recommendation.frame.model_no or "ブランド"
            shape_name = primary_recommendation.frame.lens_shape_name or "クラシック"
            material_text = "プレミアム"  # デフォルト値
            color_text = primary_recommendation.frame.color_name or "ナチュラル"
            
            style_explanation = f"{brand_name}の{shape_name}スタイルは、あなたの好みに合わせた洗練されたデザインです。{material_text}素材と{color_text}カラーの組み合わせが、あなたの個性を引き立てます。日常使いからビジネスシーンまで幅広く活躍します。"
        
        # 特徴ハイライトを生成
        feature_highlights = []
        if primary_recommendation and primary_recommendation.frame:
            if primary_recommendation.frame.material:
                feature_highlights.append(f"{primary_recommendation.frame.material}素材")
            if primary_recommendation.frame.display_shape:
                feature_highlights.append(f"{primary_recommendation.frame.display_shape}シェイプ")
            if primary_recommendation.frame.display_color:
                feature_highlights.append(f"{primary_recommendation.frame.display_color}カラー")
                
        # デフォルトの特徴がない場合
        if not feature_highlights:
            feature_highlights = ["クラシックデザイン", "高品質素材", "快適なフィット感"]
        
        # スタイルカテゴリを決定
        style_category = style_preference.preferred_styles[0] if style_preference and style_preference.preferred_styles else "クラシック"
        
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
        
        # デバッグ情報: 推奨されたフレームの詳細情報をログに出力
        logger.info(f"推奨フレーム数: {len(ranked_frames)}")
        for i, rec in enumerate(ranked_frames[:5]):
            frame = rec.frame
            logger.info(f"フレーム {i+1}: ID={frame.id}, 名前={frame.name}, ブランド={frame.brand}, "
                        f"スコア={rec.total_score:.2f}, フィットスコア={rec.fit_score:.2f}, "
                        f"スタイルスコア={rec.style_score:.2f}")
            
            # フレームにNoneのリストフィールドがあるか確認
            has_none_fields = []
            if frame.face_shape_types is None:
                has_none_fields.append("face_shape_types")
            if frame.style_tags is None:
                has_none_fields.append("style_tags")
            if frame.image_urls is None:
                has_none_fields.append("image_urls")
                
            if has_none_fields:
                logger.warning(f"フレーム {frame.id} には None のリストフィールドがあります: {', '.join(has_none_fields)}")
                
            # 空のリストフィールドをデフォルト値で埋める
            # これはレスポンスを変更するものではなく、ログ記録のためのものです
        
        logger.info(f"メガネフレーム推薦レスポンス生成完了: 主要推薦={response.primary_recommendation.frame.name}, "
                   f"代替推薦数={len(response.alternative_recommendations)}")
        
        return response
        
    except Exception as e:
        logger.error(f"メガネフレーム推薦処理エラー: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"推薦の処理中にエラーが発生しました: {str(e)}")

# OPTIONSメソッドのハンドラを追加
@router.options("/glasses")
def options_glasses_recommendation():
    """メガネ推薦エンドポイントのOPTIONSリクエストハンドラー"""
    logger.info("メガネ推薦エンドポイントへのOPTIONSリクエスト受信")
    return {
        "Allow": "POST, OPTIONS",
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
        "Access-Control-Max-Age": "3600"
    }
