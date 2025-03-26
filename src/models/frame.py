from sqlalchemy import Column, Integer, String, Float, DateTime, JSON
from sqlalchemy.sql import func
from ..database import Base

class Frame(Base):
    __tablename__ = "frames"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    brand = Column(String(255), nullable=False)
    price = Column(Integer, nullable=False)
    style = Column(String(255))
    shape = Column(String(255))
    material = Column(String(255))
    color = Column(String(255))
    
    # サイズ情報
    frame_width = Column(Float)
    lens_width = Column(Float)
    bridge_width = Column(Float)
    temple_length = Column(Float)
    lens_height = Column(Float)
    weight = Column(Float)

    # 推奨情報
    recommended_face_width_min = Column(Float)
    recommended_face_width_max = Column(Float)
    recommended_nose_height_min = Column(Float)
    recommended_nose_height_max = Column(Float)
    
    # スタイル情報
    personal_color_season = Column(String(255))
    face_shape_types = Column(JSON)
    style_tags = Column(JSON)
    
    # 画像情報
    image_urls = Column(JSON)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now()) 