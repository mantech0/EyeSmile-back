from sqlalchemy.orm import Session
import logging
import math
from typing import List, Dict, Any, Tuple, Optional
from .. import models, schemas
from .frame import get_frames, get_recommended_frames

# ロガーの設定
logger = logging.getLogger(__name__)

# 顔の形状分析
def analyze_face_shape(face_data: schemas.FaceMeasurement) -> str:
    """顔の形状を分析する"""
    # 顔の縦横比を計算
    width_to_height_ratio = face_data.face_width / face_data.nose_height
    
    # 頬の面積を考慮
    cheek_factor = face_data.cheek_area / (face_data.face_width * face_data.nose_height)
    
    # 眉間の位置を考慮
    temple_factor = face_data.temple_position / face_data.face_width
    
    # 顔の形状を判定
    if width_to_height_ratio > 1.1:  # 横長の顔
        if cheek_factor > 0.3:
            return "丸顔"
        else:
            return "四角顔"
    elif width_to_height_ratio < 0.9:  # 縦長の顔
        if temple_factor > 0.6:
            return "逆三角顔"
        else:
            return "卵型顔"
    else:  # バランスの取れた顔
        if cheek_factor > 0.3:
            return "楕円顔"
        else:
            return "ダイヤモンド顔"

# スタイルカテゴリの判定
def determine_style_category(face_shape: str, style_pref: Optional[schemas.StylePreference]) -> str:
    """スタイルカテゴリを判定する"""
    if not style_pref or not style_pref.preferred_styles:
        # デフォルトのスタイル推奨
        style_map = {
            "丸顔": "シャープ",
            "四角顔": "ソフト",
            "逆三角顔": "バランス",
            "卵型顔": "クラシック",
            "楕円顔": "モダン",
            "ダイヤモンド顔": "エレガント"
        }
        return style_map.get(face_shape, "クラシック")
    
    # ユーザー設定からスタイルを判定
    style_count = {}
    for style in style_pref.preferred_styles:
        if "カジュアル" in style:
            style_count["カジュアル"] = style_count.get("カジュアル", 0) + 1
        if "フォーマル" in style:
            style_count["フォーマル"] = style_count.get("フォーマル", 0) + 1
        # 他のスタイルも同様に分類
    
    # 最も多いスタイルを返す
    if style_count:
        return max(style_count.items(), key=lambda x: x[1])[0]
    
    return "クラシック"  # デフォルト

# フィットスコアの計算
def calculate_fit_score(face_data: schemas.FaceMeasurement, frame: models.Frame) -> float:
    """フレームと顔のフィット度を計算"""
    score = 100.0  # 初期スコア
    
    # 顔幅に基づくスコア調整
    if frame.recommended_face_width_min and frame.recommended_face_width_max:
        if face_data.face_width < frame.recommended_face_width_min:
            # 顔が細すぎる
            diff_ratio = (frame.recommended_face_width_min - face_data.face_width) / frame.recommended_face_width_min
            score -= diff_ratio * 30
        elif face_data.face_width > frame.recommended_face_width_max:
            # 顔が広すぎる
            diff_ratio = (face_data.face_width - frame.recommended_face_width_max) / frame.recommended_face_width_max
            score -= diff_ratio * 30
        else:
            # 理想的な範囲内
            mid_point = (frame.recommended_face_width_min + frame.recommended_face_width_max) / 2
            diff_ratio = abs(face_data.face_width - mid_point) / (frame.recommended_face_width_max - frame.recommended_face_width_min)
            score += (1 - diff_ratio) * 10
    
    # 鼻の高さに基づくスコア調整（同様に計算）
    if frame.recommended_nose_height_min and frame.recommended_nose_height_max:
        if face_data.nose_height < frame.recommended_nose_height_min:
            diff_ratio = (frame.recommended_nose_height_min - face_data.nose_height) / frame.recommended_nose_height_min
            score -= diff_ratio * 20
        elif face_data.nose_height > frame.recommended_nose_height_max:
            diff_ratio = (face_data.nose_height - frame.recommended_nose_height_max) / frame.recommended_nose_height_max
            score -= diff_ratio * 20
        else:
            mid_point = (frame.recommended_nose_height_min + frame.recommended_nose_height_max) / 2
            diff_ratio = abs(face_data.nose_height - mid_point) / (frame.recommended_nose_height_max - frame.recommended_nose_height_min)
            score += (1 - diff_ratio) * 5
    
    # その他の要素も考慮できる
    # 例: 目の間隔とフレーム幅の関係
    
    # スコアを0〜100の範囲に収める
    return max(0, min(100, score))

# スタイルスコアの計算
def calculate_style_score(
    face_shape: str, 
    style_category: str,
    frame: models.Frame,
    style_pref: Optional[schemas.StylePreference]
) -> float:
    """フレームとスタイル好みの一致度を計算"""
    score = 70.0  # 基本スコア
    
    # 顔の形に対する最適なフレーム形状
    optimal_shapes = {
        "丸顔": ["スクエア", "長方形", "ウェリントン"],
        "四角顔": ["ラウンド", "オーバル", "キャットアイ"],
        "逆三角顔": ["ブロー", "クラブマスター", "アビエーター"],
        "卵型顔": ["すべて"],  # 卵型は多くの形状に適合
        "楕円顔": ["スクエア", "長方形", "ウェリントン"],
        "ダイヤモンド顔": ["オーバル", "キャットアイ"]
    }
    
    # フレーム形状に基づくスコア調整
    recommended_shapes = optimal_shapes.get(face_shape, ["すべて"])
    if "すべて" in recommended_shapes or frame.shape in recommended_shapes:
        score += 15
    
    # パーソナルカラーの一致度
    if style_pref and style_pref.personal_color and frame.personal_color_season:
        if style_pref.personal_color == frame.personal_color_season:
            score += 10
    
    # スタイルタグの一致度
    if style_pref and style_pref.preferred_styles and frame.style_tags:
        matching_styles = set(style_pref.preferred_styles) & set(frame.style_tags)
        style_match_score = len(matching_styles) * 5  # 一致するスタイルごとに5点加算
        score += min(15, style_match_score)  # 最大15点まで
    
    # 素材の好みとの一致
    if style_pref and style_pref.preferred_materials and frame.material:
        if frame.material in style_pref.preferred_materials:
            score += 5
    
    # 色の好みとの一致
    if style_pref and style_pref.preferred_colors and frame.color:
        if frame.color in style_pref.preferred_colors:
            score += 5
    
    # スコアを0〜100の範囲に収める
    return max(0, min(100, score))

# 推薦理由の生成
def generate_recommendation_reason(
    face_shape: str,
    style_category: str,
    fit_score: float,
    style_score: float,
    frame: models.Frame
) -> str:
    """推薦理由を生成する"""
    
    reasons = []
    
    # フィット感に関する理由
    if fit_score > 85:
        reasons.append(f"あなたの顔の形状({face_shape})に完璧にフィットします")
    elif fit_score > 70:
        reasons.append(f"あなたの顔の形状({face_shape})に適したサイズとデザインです")
    else:
        reasons.append(f"あなたの顔の形状({face_shape})に対して調和のとれたバランスを提供します")
    
    # スタイルに関する理由
    if style_score > 85:
        reasons.append(f"あなたの好みの{style_category}スタイルに最適です")
    elif style_score > 70:
        reasons.append(f"あなたの{style_category}スタイルを引き立てます")
    else:
        reasons.append(f"{style_category}な印象を与えるデザインです")
    
    # フレーム特有の特徴
    if frame.material:
        reasons.append(f"{frame.material}素材による快適な装着感")
    
    if frame.style:
        reasons.append(f"{frame.style}スタイルのデザイン")
    
    return "このフレームは" + "、".join(reasons) + "。"

# 推薦詳細の生成
def generate_recommendation_details(
    face_data: schemas.FaceMeasurement,
    face_shape: str,
    style_category: str,
    frame: models.Frame,
    fit_score: float,
    style_score: float
) -> schemas.RecommendationDetails:
    """推薦の詳細な説明を生成する"""
    
    # フィット説明
    fit_explanations = {
        "丸顔": "丸顔の方には角張ったフレームがおすすめです。シャープな印象を与え、顔の丸みとバランスを取ります。",
        "四角顔": "四角顔の方には丸みのあるフレームがおすすめです。顔の角張った印象を和らげます。",
        "逆三角顔": "逆三角顔の方にはボトムが強調されたフレームがおすすめです。顔の下部にボリュームを持たせます。",
        "卵型顔": "卵型顔の方には多くのスタイルが似合います。バランスの取れた顔立ちを活かすデザインがおすすめです。",
        "楕円顔": "楕円顔の方には幾何学的なデザインがおすすめです。顔の特徴を引き立てます。",
        "ダイヤモンド顔": "ダイヤモンド顔の方には上部が強調されたフレームがおすすめです。顔の特徴的な骨格を引き立てます。"
    }
    
    fit_explanation = fit_explanations.get(face_shape, "あなたの顔立ちに合わせたフレームデザインです。")
    fit_explanation += f" このフレームは顔幅と鼻の高さのバランスが{int(fit_score)}%マッチしています。"
    
    # スタイル説明
    style_explanation = f"あなたの{style_category}なイメージに{int(style_score)}%マッチしています。"
    if frame.personal_color_season:
        style_explanation += f" {frame.personal_color_season}シーズンのパーソナルカラーにも適しています。"
    
    # 特筆すべき特徴
    feature_highlights = []
    if frame.material:
        feature_highlights.append(f"{frame.material}素材を使用")
    if frame.shape:
        feature_highlights.append(f"{frame.shape}シェイプのデザイン")
    if frame.brand:
        feature_highlights.append(f"{frame.brand}ブランドの品質")
    if frame.weight and frame.weight < 20:
        feature_highlights.append("軽量設計で長時間の着用も快適")
    
    # 少なくとも3つの特徴を提供
    if len(feature_highlights) < 3:
        additional_features = [
            "UVカットレンズ対応",
            "高品質な仕上げ",
            "調整可能なノーズパッド"
        ]
        feature_highlights.extend(additional_features[:3 - len(feature_highlights)])
    
    return schemas.RecommendationDetails(
        fit_explanation=fit_explanation,
        style_explanation=style_explanation,
        feature_highlights=feature_highlights
    )

# メイン推薦機能
def get_frame_recommendations(
    db: Session,
    request: schemas.recommendation.RecommendationRequest,
    limit: int = 5
) -> schemas.RecommendationResponse:
    """顔データとスタイル好みに基づいてフレームを推薦"""
    try:
        # リクエストから顔データとスタイル好みを取得
        face_data = request.face_data
        style_preference = request.style_preference
        
        # 顔の形状分析
        face_shape = analyze_face_shape(face_data)
        
        # スタイルカテゴリの判定
        style_category = determine_style_category(face_shape, style_preference)
        
        # 顔分析結果
        face_analysis = {
            "face_shape": face_shape,
            "style_category": style_category,
            "measurements": {
                "face_width": face_data.face_width,
                "eye_distance": face_data.eye_distance,
                "nose_height": face_data.nose_height
            }
        }
        
        # 推奨フレームの取得（フィルタリング）
        style_preferences = []
        if style_preference and style_preference.preferred_styles:
            style_preferences = style_preference.preferred_styles
            
        personal_color = None
        if style_preference and style_preference.personal_color:
            personal_color = style_preference.personal_color
            
        frames = get_recommended_frames(
            db=db,
            face_width=face_data.face_width,
            nose_height=face_data.nose_height,
            personal_color=personal_color,
            style_preferences=style_preferences,
            limit=limit * 2  # より多くの候補を取得
        )
        
        # 候補がない場合、全てのフレームから選択
        if not frames:
            logger.warning("推奨条件に一致するフレームがありません。すべてのフレームから選択します。")
            frames = get_frames(db=db, limit=limit * 3)
        
        # フレームの評価とランキング
        ranked_frames = []
        for frame in frames:
            fit_score = calculate_fit_score(face_data, frame)
            style_score = calculate_style_score(face_shape, style_category, frame, style_preference)
            total_score = (fit_score * 0.6) + (style_score * 0.4)  # 重み付け
            
            reason = generate_recommendation_reason(
                face_shape, style_category, fit_score, style_score, frame
            )
            
            ranked_frames.append({
                "frame": frame,
                "fit_score": fit_score,
                "style_score": style_score,
                "total_score": total_score,
                "reason": reason
            })
        
        # スコアでソート
        ranked_frames.sort(key=lambda x: x["total_score"], reverse=True)
        
        # 最適なフレームと代替フレームを選択
        primary = ranked_frames[0] if ranked_frames else None
        alternatives = ranked_frames[1:limit] if len(ranked_frames) > 1 else []
        
        if not primary:
            raise ValueError("適切なフレームが見つかりませんでした")
        
        # プライマリ推薦のレスポンス
        primary_recommendation = schemas.FrameRecommendationResponse(
            frame=primary["frame"],
            fit_score=primary["fit_score"],
            style_score=primary["style_score"],
            total_score=primary["total_score"],
            recommendation_reason=primary["reason"]
        )
        
        # 代替推薦のレスポンス
        alternative_recommendations = [
            schemas.FrameRecommendationResponse(
                frame=alt["frame"],
                fit_score=alt["fit_score"],
                style_score=alt["style_score"],
                total_score=alt["total_score"],
                recommendation_reason=alt["reason"]
            )
            for alt in alternatives
        ]
        
        # 推薦詳細の生成
        recommendation_details = generate_recommendation_details(
            face_data,
            face_shape,
            style_category,
            primary["frame"],
            primary["fit_score"],
            primary["style_score"]
        )
        
        # 最終レスポンスの構築
        return schemas.RecommendationResponse(
            primary_recommendation=primary_recommendation,
            alternative_recommendations=alternative_recommendations,
            face_analysis=face_analysis,
            recommendation_details=recommendation_details
        )
        
    except Exception as e:
        logger.error(f"フレーム推薦中にエラーが発生しました: {str(e)}", exc_info=True)
        raise 