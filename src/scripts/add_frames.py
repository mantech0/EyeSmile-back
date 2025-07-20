import sys
import os

# 親ディレクトリをパスに追加して、srcモジュールをインポートできるようにする
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))

from src.database import get_db
from src.models.frame import Frame

def add_frames():
    # データベースセッションを取得
    db = next(get_db())
    
    # 既存のフレームデータをクリア
    try:
        db.query(Frame).delete()
        db.commit()
        print("既存のフレームデータをクリアしました")
    except Exception as e:
        db.rollback()
        print(f"データクリア中にエラーが発生しました: {e}")

    # 新しいフレームデータを追加
    frames = [
        {
            'name': 'クラシック ボストン',
            'brand': 'EyeSmile',
            'price': 19800,
            'description': 'クラシックなボストンデザイン',
            'style': 'クラシック',
            'shape': 'ボストン',
            'color': 'ブラック',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ191007_14F1_3.png',
            'status': 'active'
        },
        {
            'name': 'モダン スクエア',
            'brand': 'EyeSmile',
            'price': 21800,
            'description': 'シャープなスクエアデザイン',
            'style': 'モダン',
            'shape': 'スクエア',
            'color': 'ブラウン',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ221012_42A1_3.png',
            'status': 'active'
        },
        {
            'name': 'ライト オーバル',
            'brand': 'EyeSmile',
            'price': 18800,
            'description': '軽量で快適なオーバルフレーム',
            'style': 'カジュアル',
            'shape': 'オーバル',
            'color': 'ブラック',
            'material': 'メタル',
            'image_url': '/images/frames-notempel/ZJ221062_14E1_3.png',
            'status': 'active'
        },
        {
            'name': 'ベーシック ラウンド',
            'brand': 'EyeSmile',
            'price': 17800,
            'description': 'ベーシックな丸型フレーム',
            'style': 'カジュアル',
            'shape': 'ラウンド',
            'color': 'ブラック',
            'material': 'メタル',
            'image_url': '/images/frames-notempel/ZJ41028_B-1_3.png',
            'status': 'active'
        },
        {
            'name': 'スタイリッシュ ハーフリム',
            'brand': 'EyeSmile',
            'price': 22800,
            'description': 'スタイリッシュなハーフリムデザイン',
            'style': 'モダン',
            'shape': 'ハーフリム',
            'color': 'シルバー',
            'material': 'メタル',
            'image_url': '/images/frames-notempel/ZJ71012_B-1A_3.png',
            'status': 'active'
        },
        {
            'name': 'エレガント クラシック',
            'brand': 'EyeSmile',
            'price': 23800,
            'description': 'エレガントなクラシックデザイン',
            'style': 'エレガント',
            'shape': 'スクエア',
            'color': 'ブラウン',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ71017_43A2_3.png',
            'status': 'active'
        },
        {
            'name': 'クラシック オーバル',
            'brand': 'EyeSmile',
            'price': 20800,
            'description': 'クラシックなオーバルデザイン',
            'style': 'クラシック',
            'shape': 'オーバル',
            'color': 'ブラック',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ71017_49A1_3.png',
            'status': 'active'
        },
        {
            'name': 'モダン ラウンド',
            'brand': 'EyeSmile',
            'price': 21800,
            'description': 'モダンな丸型フレーム',
            'style': 'モダン',
            'shape': 'ラウンド',
            'color': 'ブラック',
            'material': 'メタル',
            'image_url': '/images/frames-notempel/ZJ71017_68E1_3.png',
            'status': 'active'
        },
        {
            'name': 'ベーシック ウェリントン',
            'brand': 'EyeSmile',
            'price': 19800,
            'description': 'ベーシックなウェリントンデザイン',
            'style': 'ベーシック',
            'shape': 'ウェリントン',
            'color': 'ブラック',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ71017_B-1_3.png',
            'status': 'active'
        },
        {
            'name': 'ライト スクエア',
            'brand': 'EyeSmile',
            'price': 18800,
            'description': '軽量なスクエアフレーム',
            'style': 'ライト',
            'shape': 'スクエア',
            'color': 'クリア',
            'material': 'プラスチック',
            'image_url': '/images/frames-notempel/ZJ71017_C-1A_3.png',
            'status': 'active'
        },
        {
            'name': 'ミニマル ラウンド',
            'brand': 'EyeSmile',
            'price': 17800,
            'description': 'ミニマルな丸型フレーム',
            'style': 'ミニマル',
            'shape': 'ラウンド',
            'color': 'ブラック',
            'material': 'メタル',
            'image_url': '/images/frames-notempel/ZJ71020_B-1_3.png',
            'status': 'active'
        }
    ]

    # データベースに追加
    try:
        for frame_data in frames:
            frame = Frame(**frame_data)
            db.add(frame)
        
        db.commit()
        
        # 確認
        count = db.query(Frame).count()
        print(f'フレームデータを{count}件追加しました')
        
        # 追加したデータの表示
        frames = db.query(Frame).all()
        for frame in frames:
            print(f'ID: {frame.id}, 名前: {frame.name}, ブランド: {frame.brand}, 画像: {frame.image_url}')
    except Exception as e:
        db.rollback()
        print(f"データ追加中にエラーが発生しました: {e}")

if __name__ == "__main__":
    add_frames() 