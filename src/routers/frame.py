from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session
from typing import List
import csv
import io
from ..database import get_db
from .. import crud, schemas
from ..utils.csv_import import validate_frame_data

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

@router.get("/", response_model=List[schemas.Frame])
def get_frames(
    skip: int = 0,
    limit: int = 100,
    brand: str = None,
    style: str = None,
    shape: str = None,
    color: str = None,
    price_min: int = None,
    price_max: int = None,
    db: Session = Depends(get_db)
):
    """フレームの一覧を取得します"""
    frames = crud.frame.get_frames(
        db,
        skip=skip,
        limit=limit,
        brand=brand,
        style=style,
        shape=shape,
        color=color,
        price_min=price_min,
        price_max=price_max
    )
    return frames

@router.get("/{frame_id}", response_model=schemas.Frame)
def get_frame(frame_id: int, db: Session = Depends(get_db)):
    """指定されたIDのフレームを取得します"""
    frame = crud.frame.get_frame(db, frame_id)
    if frame is None:
        raise HTTPException(status_code=404, detail="フレームが見つかりません")
    return frame 