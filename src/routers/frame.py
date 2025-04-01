from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Response, Query
from sqlalchemy.orm import Session
from typing import List, Optional
import csv
import io
import logging
from ..database import get_db
from .. import crud, schemas
from ..utils.csv_import import validate_frame_data

# ロガーの設定
logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/frames",
    tags=["frames"]
)

@router.post("/import", response_model=List[schemas.Frame])
async def import_frames_from_csv(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """CSVファイルからフレームデータをインポートします"""
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="CSVファイルのみ対応しています")

    try:
        # CSVファイルの内容を読み込む
        content = await file.read()
        csv_text = content.decode('utf-8')
        csv_reader = csv.DictReader(io.StringIO(csv_text))
        
        imported_frames = []
        for row in csv_reader:
            try:
                # データの検証と変換
                validated_data = validate_frame_data(row)
                
                # フレームの作成
                frame_create = schemas.FrameCreate(**validated_data)
                db_frame = crud.frame.create_frame(db, frame_create)
                imported_frames.append(db_frame)
            except ValueError as e:
                # 個別の行のエラーをスキップして続行
                print(f"行のインポートに失敗: {str(e)}")
                continue
        
        return imported_frames
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"インポートに失敗しました: {str(e)}")

@router.get("", response_model=List[schemas.Frame])
def get_frames(
    skip: int = 0,
    limit: int = 100,
    brand: Optional[str] = None,
    style: Optional[str] = None,
    shape: Optional[str] = None,
    color: Optional[str] = None,
    price_min: Optional[int] = None,
    price_max: Optional[int] = None,
    db: Session = Depends(get_db),
    response: Response = None
):
    """メガネフレームの一覧を取得します"""
    # CORSヘッダーを追加
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "3600"
    
    try:
        logger.info(f"フレーム一覧リクエスト: skip={skip}, limit={limit}, brand={brand}, style={style}, shape={shape}, color={color}, price_min={price_min}, price_max={price_max}")
        
        frames = crud.frame.get_frames(
            db=db,
            skip=skip,
            limit=limit,
            brand=brand,
            style=style,
            shape=shape,
            color=color,
            price_min=price_min,
            price_max=price_max
        )
        
        logger.info(f"{len(frames)}件のフレームデータを取得しました")
        return frames
        
    except Exception as e:
        logger.error(f"フレームデータ取得中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"フレームデータの取得中にエラーが発生しました: {str(e)}"
        )

@router.get("/{frame_id}", response_model=schemas.Frame)
def get_frame(
    frame_id: int,
    db: Session = Depends(get_db),
    response: Response = None
):
    """指定されたIDのメガネフレームを取得します"""
    # CORSヘッダーを追加
    if response:
        response.headers["Access-Control-Allow-Origin"] = "*"
        response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
        response.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization, X-Requested-With"
        response.headers["Access-Control-Max-Age"] = "3600"
    
    try:
        logger.info(f"フレーム詳細リクエスト: id={frame_id}")
        
        frame = crud.frame.get_frame(db=db, frame_id=frame_id)
        if frame is None:
            raise HTTPException(
                status_code=404,
                detail=f"ID {frame_id} のフレームは見つかりませんでした"
            )
        
        logger.info(f"フレームデータを取得しました: id={frame.id}, name={frame.name}")
        return frame
        
    except HTTPException as he:
        # 既に適切なHTTPExceptionが発生している場合はそのまま再raise
        raise he
    except Exception as e:
        logger.error(f"フレームデータ取得中にエラーが発生しました: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"フレームデータの取得中にエラーが発生しました: {str(e)}"
        )

@router.options("")
def options_frames():
    """フレーム一覧エンドポイントのOPTIONSリクエストハンドラー"""
    logger.info("フレーム一覧エンドポイントへのOPTIONSリクエスト受信")
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "3600",
        },
    )

@router.options("/{frame_id}")
def options_frame_detail(frame_id: int):
    """フレーム詳細エンドポイントのOPTIONSリクエストハンドラー"""
    logger.info(f"フレーム詳細エンドポイントへのOPTIONSリクエスト受信: id={frame_id}")
    return Response(
        content="",
        headers={
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Methods": "GET, OPTIONS",
            "Access-Control-Allow-Headers": "Content-Type, Authorization, X-Requested-With",
            "Access-Control-Max-Age": "3600",
        },
    ) 