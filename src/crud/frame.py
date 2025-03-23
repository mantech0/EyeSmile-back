from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from .. import models, schemas

def create_frame(db: Session, frame: schemas.FrameCreate) -> models.Frame:
    db_frame = models.Frame(**frame.model_dump())
    db.add(db_frame)
    db.commit()
    db.refresh(db_frame)
    return db_frame

def get_frame(db: Session, frame_id: int) -> Optional[models.Frame]:
    return db.query(models.Frame).filter(models.Frame.id == frame_id).first()

def get_frames(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    style: Optional[str] = None,
    shape: Optional[str] = None,
    color: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None
) -> List[models.Frame]:
    query = db.query(models.Frame)
    
    if brand:
        query = query.filter(models.Frame.brand == brand)
    if style:
        query = query.filter(models.Frame.style == style)
    if shape:
        query = query.filter(models.Frame.shape == shape)
    if color:
        query = query.filter(models.Frame.color == color)
    if price_min is not None:
        query = query.filter(models.Frame.price >= price_min)
    if price_max is not None:
        query = query.filter(models.Frame.price <= price_max)
    
    return query.offset(skip).limit(limit).all()

def update_frame(
    db: Session,
    frame_id: int,
    frame_update: schemas.FrameCreate
) -> Optional[models.Frame]:
    db_frame = get_frame(db, frame_id)
    if db_frame:
        for key, value in frame_update.model_dump().items():
            setattr(db_frame, key, value)
        db.commit()
        db.refresh(db_frame)
    return db_frame

def delete_frame(db: Session, frame_id: int) -> bool:
    db_frame = get_frame(db, frame_id)
    if db_frame:
        db.delete(db_frame)
        db.commit()
        return True
    return False

def get_recommended_frames(
    db: Session,
    face_width: float,
    nose_height: float,
    personal_color: Optional[str] = None,
    style_preferences: List[str] = [],
    limit: int = 10
) -> List[models.Frame]:
    query = db.query(models.Frame)
    
    # 基本的なフィット条件
    query = query.filter(
        models.Frame.recommended_face_width_min <= face_width,
        models.Frame.recommended_face_width_max >= face_width,
        models.Frame.recommended_nose_height_min <= nose_height,
        models.Frame.recommended_nose_height_max >= nose_height
    )
    
    # パーソナルカラーによるフィルタリング
    if personal_color:
        query = query.filter(models.Frame.personal_color_season == personal_color)
    
    # スタイル設定によるフィルタリング
    if style_preferences:
        for style in style_preferences:
            query = query.filter(models.Frame.style_tags.contains([style]))
    
    return query.limit(limit).all() 