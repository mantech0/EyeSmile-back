from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Table
from sqlalchemy.sql import func
from sqlalchemy.ext.hybrid import hybrid_property
from ..database import Base

class Frame(Base):
    __tablename__ = "frames"
    __table_args__ = {'extend_existing': True}

    # 主キー
    id = Column(Integer, primary_key=True, index=True)
    
    # Azure MySQL DBのカラム名に合わせる
    # ローカルアプリが期待するプロパティ名をAzure DBの実際のカラム名にマッピング
    product_name = Column(String(255), nullable=True)  # nameのかわりに使用
    model_no = Column(String(50), nullable=True)       # brandのかわりに使用
    rank = Column(Integer, nullable=True)              # priceのかわりに使用×100
    lens_shape_name = Column(String(50), nullable=True)  # shapeのかわりに使用
    color_name = Column(String(50), nullable=True)     # colorのかわりに使用
    size_name = Column(String(10), nullable=True)      
    bridge_size = Column(Float, nullable=True)         # bridge_widthのかわりに使用
    temple_size = Column(Float, nullable=True)         # temple_lengthのかわりに使用
    height_mm = Column(Float, nullable=True)           # lens_heightのかわりに使用
    width_mm = Column(Float, nullable=True)            # frame_widthのかわりに使用
    lens_height = Column(Float, nullable=True)         
    lens_width = Column(Float, nullable=True)
    weight = Column(String(20), nullable=True)
    total_sales = Column(Integer, nullable=True)
    
    # 以下は実際のDBには存在しないが、コード互換性のためにマッピングする
    # SQLAlchemyはこれらのカラムをSELECTしようとするがDBには存在しない
    name = None
    brand = None
    price = None
    style = None
    shape = None
    material = None
    color = None
    frame_width = None
    bridge_width = None
    temple_length = None
    description = Column(String(500), nullable=True)
    recommended_face_width_min = Column(Float, nullable=True)
    recommended_face_width_max = Column(Float, nullable=True)
    recommended_nose_height_min = Column(Float, nullable=True)
    recommended_nose_height_max = Column(Float, nullable=True)
    personal_color_season = Column(String(255), nullable=True)
    face_shape_types = Column(JSON, nullable=True)
    style_tags = Column(JSON, nullable=True)
    image_url = Column(String(500), nullable=True)
    image_urls = Column(JSON, nullable=True)
    status = Column(String(20), nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 
    
    # ハイブリッドプロパティ - SQLではなくPythonで計算（カラムが存在しなくてもアクセス可能）
    @hybrid_property
    def name(self):
        """名前を返す"""
        return self.product_name
    
    @hybrid_property
    def brand(self):
        """ブランド名を返す"""
        return self.model_no
    
    @hybrid_property
    def shape(self):
        """形状を返す"""
        return self.lens_shape_name
    
    @hybrid_property
    def color(self):
        """色を返す"""
        return self.color_name
        
    @hybrid_property
    def price(self):
        """価格を計算して返す"""
        if self.rank is not None:
            return self.rank * 1000
        return 15000  # デフォルト価格
    
    @hybrid_property
    def frame_width(self):
        """フレーム幅を返す"""
        return self.width_mm
    
    @hybrid_property
    def bridge_width(self):
        """ブリッジ幅を返す"""
        return self.bridge_size
    
    @hybrid_property
    def temple_length(self):
        """テンプル長を返す"""
        return self.temple_size
    
    def __init__(self, **kwargs):
        # JSONフィールドのNoneを空リストに設定
        kwargs.setdefault('face_shape_types', [])
        kwargs.setdefault('style_tags', [])
        kwargs.setdefault('image_urls', [])
        
        # Noneの場合は空リストに変換
        if kwargs.get('face_shape_types') is None:
            kwargs['face_shape_types'] = []
        if kwargs.get('style_tags') is None:
            kwargs['style_tags'] = []
        if kwargs.get('image_urls') is None:
            kwargs['image_urls'] = []
            
        super().__init__(**kwargs) 