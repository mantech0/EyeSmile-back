import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src.database import SessionLocal
from src.utils.data_converter import convert_csv_to_frames
from src.models.user import Frame
from sqlalchemy.exc import SQLAlchemyError

def import_frames():
    """フレームデータをデータベースにインポートします"""
    csv_path = os.path.join('data', 'private', 'frames.csv')
    
    if not os.path.exists(csv_path):
        print(f"Error: CSVファイルが見つかりません: {csv_path}")
        return
    
    try:
        # CSVデータの変換
        frames_data = convert_csv_to_frames(csv_path)
        print(f"変換されたフレーム数: {len(frames_data)}")
        
        # データベースセッションの作成
        db = SessionLocal()
        
        try:
            # 既存のフレームデータをクリア
            db.query(Frame).delete()
            
            # 新しいフレームデータの挿入
            for frame_data in frames_data:
                frame = Frame(**frame_data)
                db.add(frame)
            
            # 変更をコミット
            db.commit()
            print("フレームデータのインポートが完了しました")
            
        except SQLAlchemyError as e:
            db.rollback()
            print(f"データベースエラー: {str(e)}")
        finally:
            db.close()
            
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")

if __name__ == "__main__":
    import_frames() 