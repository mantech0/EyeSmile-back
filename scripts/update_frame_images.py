#!/usr/bin/env python3
import sys
import os
import json
from sqlalchemy.orm import Session
from sqlalchemy import text

# プロジェクトルートをPythonパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import SessionLocal
from src.models.frame import Frame

# 環境変数
is_production = os.environ.get("PRODUCTION", "false").lower() == "true"
# 本番環境のベースURL (実際にデプロイする際に変更してください)
PRODUCTION_BASE_URL = "https://eyesmile-prod.azurewebsites.net"

# 画像マッピング - キーはブランドと形状のペア、値は実際の画像ファイル名（真正面からの画像）
IMAGE_MAPPINGS = {
    ("Zoff", "ラウンド"): "/images/frames/zoff-sporty-round.jpg",
    ("Zoff", "スクエア"): "/images/frames/zoff-classic-square.jpg",
    ("Zoff", "オーバル"): "/images/frames/zoff-elegant-oval.jpg",
    ("JINS", "スクエア"): "/images/frames/jins-classic-square.jpg",
    ("JINS", "ラウンド"): "/images/frames/jins-modern-round.jpg",
    ("Persol", "ウェリントン"): "/images/frames/persol-modern-wellington.jpg",
    ("Ray-Ban", "ウェイファーラー"): "/images/frames/ray-ban-wayfarer.jpg",
    ("Tom Ford", "オーバル"): "/images/frames/tom-ford-oval.jpg",
    ("Oakley", "スポーティ"): "/images/frames/oakley-sporty.jpg",
}

def generate_filename(brand, product_name, style):
    """ブランド名と商品名からファイル名を生成"""
    # ブランドと商品名を小文字に変換し、スペースをハイフンに置換
    brand_clean = brand.lower().replace(' ', '-')
    style_clean = style.lower().replace(' ', '-')
    
    # 商品名から適切なファイル名を生成
    filename = f"{brand_clean}-{style_clean}.jpg"
    return filename

def update_frame_images():
    """フレームの画像URLを更新する"""
    db = SessionLocal()
    updated_count = 0
    
    try:
        # すべてのフレームを取得
        frames = db.query(Frame).all()
        print(f"合計フレーム数: {len(frames)}")
        
        for frame in frames:
            # ブランドと形状に基づいて画像を割り当て
            brand_shape_key = (frame.brand, frame.shape)
            
            # 商品名から生成したファイル名（真正面からの画像）
            filename = generate_filename(frame.brand, frame.name, frame.style)
            default_image = f"/images/frames/{filename}"
            
            if brand_shape_key in IMAGE_MAPPINGS:
                # 特定のマッピングがある場合はそれを使用
                image_url = IMAGE_MAPPINGS[brand_shape_key]
            else:
                # マッピングがない場合は生成したファイル名を使用
                image_url = default_image
            
            # 本番環境の場合は絶対URLにする
            if is_production:
                image_url = f"{PRODUCTION_BASE_URL}{image_url}"
            
            # スラッシュ区切りからファイル名を取得して、_2付きの名前を作成（斜め表示用）
            filename_only = os.path.basename(image_url)
            base_name, ext = os.path.splitext(filename_only)
            angle_image_url = image_url.replace(filename_only, f"{base_name}_2{ext}")
            
            # JSON文字列からリストに変換して最初の要素を更新
            if frame.image_urls:
                try:
                    # すでにJSON文字列の場合
                    if isinstance(frame.image_urls, str):
                        urls = json.loads(frame.image_urls)
                    else:
                        # すでにリストの場合
                        urls = frame.image_urls
                        
                    # 画像URLを更新（真正面からの画像のみ使用）
                    if len(urls) > 0:
                        urls[0] = image_url  # 最初は真正面画像
                        
                        # 他の画像が必要な場合は同じ画像を使用
                        while len(urls) < 3:
                            urls.append(image_url)
                    else:
                        urls = [image_url, image_url, image_url]
                    
                    # 更新したURLをフレームに設定
                    frame.image_urls = urls
                    updated_count += 1
                    
                except (json.JSONDecodeError, TypeError) as e:
                    print(f"エラー: '{frame.name}'の画像URL解析に失敗しました: {e}")
                    # エラーが発生した場合は新しいリストを作成
                    frame.image_urls = [image_url, image_url, image_url]
                    updated_count += 1
            else:
                # 画像URLがまだ設定されていない場合は新しいリストを作成
                frame.image_urls = [image_url, image_url, image_url]
                updated_count += 1
        
        # 変更をコミット
        db.commit()
        print(f"更新されたフレーム数: {updated_count}")
        print("注意: 真正面からの画像のみ使用するように設定しました。")
        
    except Exception as e:
        db.rollback()
        print(f"エラーが発生しました: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    update_frame_images() 