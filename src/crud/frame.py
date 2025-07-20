from sqlalchemy.orm import Session
from sqlalchemy import desc
from typing import List, Optional
from .. import models, schemas
from sqlalchemy.sql import func, text
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

def create_frame(db: Session, frame: schemas.FrameCreate) -> models.Frame:
    db_frame = models.Frame(**frame.model_dump())
    db.add(db_frame)
    db.commit()
    db.refresh(db_frame)
    return db_frame

def get_frame(db: Session, frame_id: int) -> Optional[models.Frame]:
    """
    指定されたIDのフレームを取得
    """
    try:
        sql = "SELECT * FROM frames WHERE id = :id"
        result = db.execute(text(sql), {"id": frame_id})
        row = result.fetchone()
        
        if not row:
            return None
        
        # 行を辞書に変換
        row_dict = {col: getattr(row, col) for col in row._fields}
        
        # Frameモデルを作成
        return models.Frame(**row_dict)
    except Exception as e:
        # エラーが発生した場合はログを出力してNoneを返す
        logger.error(f"フレーム取得エラー: {e}, id={frame_id}")
        return None

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
    """
    フレームの一覧を取得
    
    NOTE: Azure MySQLとの互換性のため、生SQLを使用
    """
    try:
        # 基本クエリ
        sql = """
        SELECT * FROM frames
        """
        
        # 絞り込み条件の配列
        conditions = []
        params = {}
        
        # フィルタ条件
    if brand:
            conditions.append("model_no = :brand")
            params['brand'] = brand
        
    if style:
            # スタイル条件は削除または修正（カラムが存在しないため）
            pass
        
    if shape:
            conditions.append("lens_shape_name = :shape")
            params['shape'] = shape
        
    if color:
            conditions.append("color_name = :color")
            params['color'] = color
        
        if price_min:
            conditions.append("rank * 1000 >= :price_min")
            params['price_min'] = price_min
        
        if price_max:
            conditions.append("rank * 1000 <= :price_max")
            params['price_max'] = price_max
        
        # 条件がある場合はWHERE句を追加
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
        
        # ページネーション
        sql += " LIMIT :limit OFFSET :skip"
        params['limit'] = limit
        params['skip'] = skip
        
        # クエリ実行
        result = db.execute(text(sql), params)
        
        # 結果を辞書のリストに変換してFrameモデルのインスタンスを作成
        frames = []
        for row in result.fetchall():
            try:
                # 行を辞書に変換
                row_dict = {col: getattr(row, col) for col in row._fields}
                
                # 辞書からFrameモデルのインスタンスを作成
                frame = models.Frame(**row_dict)
                frames.append(frame)
            except Exception as e:
                # エラーが発生した場合はログを出力してスキップ
                logger.error(f"フレーム作成エラー: {e}")
                continue
        
        return frames
    except Exception as e:
        logger.error(f"フレーム一覧取得エラー: {e}")
        return []

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
    try:
        # カスタムSQLを使用して互換性の問題を回避
        sql = """
        SELECT * FROM frames 
        """
        
        conditions = []
        params = {}
        
        # 基本的なフィット条件（範囲を広く設定）
        width_buffer = 30.0   # 30mmの許容範囲
        height_buffer = 20.0  # 20mmの許容範囲
        
        # サイズフィルタリングを条件に追加
        if face_width:
            conditions.append("""
                (recommended_face_width_min IS NULL OR recommended_face_width_min <= :face_width_plus) AND
                (recommended_face_width_max IS NULL OR recommended_face_width_max >= :face_width_minus)
            """)
            params['face_width_plus'] = face_width + width_buffer
            params['face_width_minus'] = face_width - width_buffer
            
        if nose_height:
            conditions.append("""
                (recommended_nose_height_min IS NULL OR recommended_nose_height_min <= :nose_height_plus) AND
                (recommended_nose_height_max IS NULL OR recommended_nose_height_max >= :nose_height_minus)
            """)
            params['nose_height_plus'] = nose_height + height_buffer
            params['nose_height_minus'] = nose_height - height_buffer
    
    # パーソナルカラーによるフィルタリング
    if personal_color:
            conditions.append("(personal_color_season IS NULL OR personal_color_season = :personal_color)")
            params['personal_color'] = personal_color
            
        # 条件がある場合はWHERE句を追加
        if conditions:
            sql += " WHERE " + " AND ".join(conditions)
            
        # ランダムに並べ替え
        sql += " ORDER BY RAND() LIMIT :limit"
        params['limit'] = limit
        
        # クエリ実行
        result = db.execute(text(sql), params)
        
        # 結果を変換
        frames = []
        for row in result.fetchall():
            try:
                # 行を辞書に変換
                row_dict = {col: getattr(row, col) for col in row._fields}
                
                # Frameモデルを作成
                frame = models.Frame(**row_dict)
                frames.append(frame)
            except Exception as e:
                logger.error(f"フレーム作成エラー: {e}")
                continue
                
        logger.info(f"推奨フレーム {len(frames)}件を取得しました")
        
        # 十分な結果が得られない場合は全てのフレームから選択
        if len(frames) < limit:
            logger.warning(f"条件に合うフレームが{len(frames)}件しか見つかりませんでした。追加のフレームを取得します。")
            
            # すでに取得したフレームIDを除外
            existing_ids = [frame.id for frame in frames]
            id_exclusion = ""
            if existing_ids:
                id_list = ",".join(str(id) for id in existing_ids)
                id_exclusion = f" WHERE id NOT IN ({id_list})"
                
            # 追加のフレームを取得
            additional_sql = f"SELECT * FROM frames{id_exclusion} ORDER BY RAND() LIMIT :limit"
            additional_result = db.execute(text(additional_sql), {"limit": limit - len(frames)})
            
            for row in additional_result.fetchall():
                try:
                    row_dict = {col: getattr(row, col) for col in row._fields}
                    frame = models.Frame(**row_dict)
                    frames.append(frame)
                except Exception as e:
                    logger.error(f"追加フレーム作成エラー: {e}")
                    continue
                    
            logger.info(f"追加の推奨フレームを含め、合計 {len(frames)}件を返します")
        
        return frames
    except Exception as e:
        logger.error(f"推奨フレーム取得エラー: {e}")
        return []