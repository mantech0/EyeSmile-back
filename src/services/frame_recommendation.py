from typing import List, Dict, Optional
from ..models import Frame, FaceMeasurement, UserResponse
from ..schemas import FrameRecommendationResponse

class FrameRecommendationService:
    # フィットスコアの重み（合計1.0）
    FIT_SCORE_WEIGHT = 0.4
    DESIGN_SCORE_WEIGHT = 0.3
    COMFORT_SCORE_WEIGHT = 0.3

    # 各測定値の理想的な比率
    IDEAL_FRAME_TO_FACE_RATIO = 0.9  # フレーム幅は顔幅の90%が理想
    IDEAL_BRIDGE_TO_EYE_RATIO = 1.0  # ブリッジ幅は目の距離と同じが理想
    IDEAL_LENS_TO_FACE_RATIO = 0.4   # レンズ高さは顔の高さの40%が理想

    @staticmethod
    def calculate_fit_score(frame: Frame, face_measurement: FaceMeasurement) -> float:
        """
        フィットスコアの計算（40%）
        - 顔幅とフレーム幅の比率（15%）
        - 目の距離とブリッジ幅の適合性（15%）
        - 顔の高さとレンズ高さの比率（10%）
        """
        # 顔幅とフレーム幅の比率スコア（0-1）
        frame_width_ratio = frame.frame_width / face_measurement.face_width
        frame_width_score = 1.0 - abs(frame_width_ratio - FrameRecommendationService.IDEAL_FRAME_TO_FACE_RATIO)
        
        # 目の距離とブリッジ幅の適合性スコア（0-1）
        bridge_ratio = frame.bridge_width / face_measurement.eye_distance
        bridge_score = 1.0 - abs(bridge_ratio - FrameRecommendationService.IDEAL_BRIDGE_TO_EYE_RATIO)
        
        # レンズ高さと顔の高さの比率スコア（0-1）
        # 注: 顔の高さは鼻の高さから推定
        estimated_face_height = face_measurement.nose_height * 2.5
        lens_height_ratio = frame.lens_height / estimated_face_height
        lens_height_score = 1.0 - abs(lens_height_ratio - FrameRecommendationService.IDEAL_LENS_TO_FACE_RATIO)

        # 重み付けしたスコアの計算
        weighted_score = (
            frame_width_score * 0.375 +  # 15% / 40% = 0.375
            bridge_score * 0.375 +       # 15% / 40% = 0.375
            lens_height_score * 0.25     # 10% / 40% = 0.25
        )

        return weighted_score

    @staticmethod
    def calculate_design_score(
        frame: Frame,
        face_measurement: FaceMeasurement,
        user_preferences: List[UserResponse]
    ) -> float:
        """
        デザインフィットスコアの計算（30%）
        - フレーム形状と顔型の相性（15%）
        - スタイルの適合性（15%）
        """
        # フレーム形状スコアの計算
        shape_score = FrameRecommendationService._calculate_shape_compatibility(
            frame.shape,
            face_measurement
        )

        # スタイル適合性スコアの計算
        style_score = FrameRecommendationService._calculate_style_compatibility(
            frame,
            user_preferences
        )

        # 両スコアを均等に重み付け
        return (shape_score + style_score) / 2

    @staticmethod
    def calculate_comfort_score(
        frame: Frame,
        face_measurement: FaceMeasurement
    ) -> float:
        """
        快適性スコアの計算（30%）
        - ノーズパッドの適合性（10%）
        - テンプル長の適合性（10%）
        - 重量バランス（10%）
        """
        # ノーズパッドスコア
        nose_pad_score = FrameRecommendationService._calculate_nose_pad_compatibility(
            frame.material,
            face_measurement.nose_height
        )

        # テンプル長スコア
        temple_score = FrameRecommendationService._calculate_temple_compatibility(
            frame.temple_length,
            face_measurement.temple_position
        )

        # 重量バランススコア
        weight_score = FrameRecommendationService._calculate_weight_balance(
            frame.weight,
            face_measurement.face_width
        )

        # 各スコアを均等に重み付け
        return (nose_pad_score + temple_score + weight_score) / 3

    @staticmethod
    def _calculate_shape_compatibility(shape: str, face_measurement: FaceMeasurement) -> float:
        """顔の形状とフレーム形状の相性を計算"""
        # 顔の形状を推定（顔幅と頬の面積から）
        face_width_to_area_ratio = face_measurement.face_width / face_measurement.cheek_area

        # 形状の相性スコアマップ
        shape_scores = {
            'round': 0.8 if face_width_to_area_ratio > 0.5 else 0.6,
            'square': 0.8 if face_width_to_area_ratio < 0.4 else 0.6,
            'oval': 0.7,  # オーバルは比較的万能
            'rectangle': 0.8 if face_width_to_area_ratio < 0.3 else 0.5,
            'cat-eye': 0.8 if face_width_to_area_ratio > 0.45 else 0.6,
        }

        return shape_scores.get(shape.lower(), 0.5)

    @staticmethod
    def _calculate_style_compatibility(
        frame: Frame,
        user_preferences: List[UserResponse]
    ) -> float:
        """スタイルの適合性を計算"""
        score = 0.5  # ベーススコア
        
        # ユーザーの好みとフレームのスタイルタグをマッチング
        matching_tags = 0
        for response in user_preferences:
            if response.preference.preference_value in frame.style_tags:
                matching_tags += 1
        
        # マッチするタグが多いほどスコアが上がる
        if matching_tags > 0:
            score += min(0.5, matching_tags * 0.1)  # 最大0.5のボーナス

        return score

    @staticmethod
    def _calculate_nose_pad_compatibility(material: str, nose_height: float) -> float:
        """ノーズパッドの適合性を計算"""
        # 鼻の高さに基づいて適切な素材を判断
        if nose_height < 10:  # 低めの鼻
            material_scores = {
                'plastic': 0.9,
                'metal': 0.6,
                'titanium': 0.7,
            }
        else:  # 高めの鼻
            material_scores = {
                'plastic': 0.7,
                'metal': 0.9,
                'titanium': 0.8,
            }
        
        return material_scores.get(material.lower(), 0.5)

    @staticmethod
    def _calculate_temple_compatibility(temple_length: float, temple_position: float) -> float:
        """テンプル長の適合性を計算"""
        # テンプル長と顔のこめかみ位置の比率を計算
        ratio = temple_length / temple_position
        
        # 理想的な比率は1.1-1.3
        if 1.1 <= ratio <= 1.3:
            return 1.0
        elif ratio < 1.1:
            return max(0.5, 1.0 - (1.1 - ratio))
        else:
            return max(0.5, 1.0 - (ratio - 1.3))

    @staticmethod
    def _calculate_weight_balance(weight: float, face_width: float) -> float:
        """重量バランスを計算"""
        # 顔の幅に対する適切な重量の範囲を設定
        ideal_weight_per_width = 0.15  # グラム/ミリメートル
        actual_weight_ratio = weight / face_width
        
        # 理想的な比率との差を計算
        difference = abs(actual_weight_ratio - ideal_weight_per_width)
        
        # 差が大きいほどスコアが下がる
        return max(0.5, 1.0 - difference)

    @staticmethod
    def get_recommendation_reason(
        frame: Frame,
        fit_score: float,
        design_score: float,
        comfort_score: float
    ) -> str:
        """推奨理由を生成"""
        reasons = []
        
        if fit_score > 0.8:
            reasons.append("顔の形状に非常に適しています")
        elif fit_score > 0.6:
            reasons.append("顔の形状によく合います")
            
        if design_score > 0.8:
            reasons.append("お好みのスタイルと完璧にマッチします")
        elif design_score > 0.6:
            reasons.append("ご希望のイメージに合っています")
            
        if comfort_score > 0.8:
            reasons.append("快適な装用感が期待できます")
        elif comfort_score > 0.6:
            reasons.append("バランスの良い掛け心地です")
            
        if not reasons:
            reasons.append("バランスの取れたフレームです")
            
        return "、".join(reasons) + "。"

    @classmethod
    def calculate_total_score(
        cls,
        frame: Frame,
        face_measurement: FaceMeasurement,
        user_preferences: List[UserResponse]
    ) -> FrameRecommendationResponse:
        """総合スコアを計算"""
        # 各スコアを計算
        fit_score = cls.calculate_fit_score(frame, face_measurement)
        design_score = cls.calculate_design_score(frame, face_measurement, user_preferences)
        comfort_score = cls.calculate_comfort_score(frame, face_measurement)
        
        # 重み付けした総合スコアを計算
        total_score = (
            fit_score * cls.FIT_SCORE_WEIGHT +
            design_score * cls.DESIGN_SCORE_WEIGHT +
            comfort_score * cls.COMFORT_SCORE_WEIGHT
        )
        
        # 推奨理由を生成
        recommendation_reason = cls.get_recommendation_reason(
            frame,
            fit_score,
            design_score,
            comfort_score
        )
        
        return FrameRecommendationResponse(
            frame=frame,
            fit_score=fit_score,
            style_score=design_score,
            total_score=total_score,
            recommendation_reason=recommendation_reason
        ) 