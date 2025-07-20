from pydantic import BaseModel, validator, root_validator, Field
from typing import List, Optional, Dict, Any, Union
from datetime import datetime

class FrameBase(BaseModel):
    # 必須フィールド（ハイブリッドフィールド - どちらのDBスキーマでも動作）
    name: Optional[str] = None
    brand: Optional[str] = None
    price: Optional[int] = 0
    style: Optional[str] = None
    shape: Optional[str] = None
    material: Optional[str] = None
    color: Optional[str] = None
    
    # Azure固有のフィールド
    product_name: Optional[str] = None
    model_no: Optional[str] = None
    lens_shape_name: Optional[str] = None
    color_name: Optional[str] = None
    size_name: Optional[str] = None
    rank: Optional[int] = None
    total_sales: Optional[int] = None
    
    # サイズ情報
    frame_width: Optional[Union[float, str]] = None  # 両方の型に対応
    lens_width: Optional[float] = 0.0
    bridge_width: Optional[float] = 0.0
    bridge_size: Optional[float] = None  # Azure互換
    temple_length: Optional[float] = 0.0
    temple_size: Optional[float] = None  # Azure互換
    lens_height: Optional[float] = 0.0
    height_mm: Optional[float] = None    # Azure互換
    width_mm: Optional[float] = None     # Azure互換
    weight: Optional[Union[float, str]] = None  # 両方の型に対応

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
    image_url: Optional[str] = None
    image_urls: List[str] = []
    
    # 表示用のプロパティ
    @property
    def display_name(self) -> str:
        """表示用の名前を返す"""
        return self.name or self.product_name or "不明"
    
    @property
    def display_brand(self) -> str:
        """ブランド名を返す"""
        return self.brand or self.model_no or "不明"
    
    @property
    def display_shape(self) -> str:
        """形状を返す"""
        return self.shape or self.lens_shape_name or "不明"
    
    @property
    def display_color(self) -> str:
        """色を返す"""
        return self.color or self.color_name or "不明"
    
    @property
    def display_price(self) -> int:
        """価格を返す - ランク×1000円のフォールバック"""
        if self.price is not None and self.price > 0:
            return self.price
        # ランクから価格を推定
        if self.rank is not None and self.rank > 0:
            return self.rank * 1000
        return 0
    
    @root_validator(pre=True)
    def handle_none_values(cls, values: Dict[str, Any]) -> Dict[str, Any]:
        # Frameオブジェクトかどうかをチェック
        if not isinstance(values, dict):
            return values
            
        # Noneのリストフィールドを空リストに変換
        for field in ['face_shape_types', 'style_tags', 'image_urls']:
            if field in values and values[field] is None:
                values[field] = []
                
        # Noneの数値フィールドをデフォルト値に変換
        number_fields = ['frame_width', 'lens_width', 'bridge_width', 'temple_length', 'lens_height', 'weight']
        for field in number_fields:
            if field in values and values[field] is None:
                values[field] = 0.0
                
        return values

class FrameCreate(FrameBase):
    pass

class Frame(FrameBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True
        
    @validator('created_at', pre=True, always=True)
    def set_created_at(cls, v):
        return v or datetime.now()
        
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        return v or datetime.now()

class FrameRecommendationResponse(BaseModel):
    frame: Frame
    fit_score: float
    style_score: float
    total_score: float
    recommendation_reason: str