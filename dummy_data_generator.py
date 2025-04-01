import os
import sys
import random
import json
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 現在のディレクトリをbackendに設定
os.chdir(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.abspath("."))

# モデルとデータベース接続をインポート
from src.database import Base, engine
from src.models.frame import Frame

# JSONエンコーダーをカスタマイズ
class DateTimeEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)

# ランダムなフレームデータを生成する関数
def generate_random_frame(id_num):
    # ブランド名のリスト
    brands = ["Zoff", "JINS", "Ray-Ban", "Oakley", "Oliver Peoples", "Tom Ford", "Persol", "Gucci"]
    
    # スタイルのリスト
    styles = ["クラシック", "モダン", "カジュアル", "ビジネス", "スポーティ", "レトロ", "ミニマル"]
    
    # シェイプのリスト
    shapes = ["ラウンド", "スクエア", "オーバル", "キャットアイ", "ティアドロップ", "ウェリントン", "ボストン", "ブロー"]
    
    # 素材のリスト
    materials = ["プラスチック", "メタル", "チタン", "アセテート", "コンビネーション"]
    
    # カラーのリスト
    colors = ["ブラック", "ブラウン", "ゴールド", "シルバー", "ブルー", "レッド", "グリーン", "クリア", "トータス"]
    
    # パーソナルカラーのリスト
    personal_colors = ["春", "夏", "秋", "冬"]
    
    # 顔の形のリスト
    face_shapes = ["丸型", "四角型", "卵型", "ハート型", "逆三角形", "長方形"]
    
    # ランダムなフレーム幅 (125-145mm)
    frame_width = round(random.uniform(125, 145), 1)
    
    # 他のサイズ情報
    lens_width = round(random.uniform(45, 55), 1)
    bridge_width = round(random.uniform(15, 22), 1)
    temple_length = round(random.uniform(135, 150), 1)
    lens_height = round(random.uniform(35, 50), 1)
    weight = round(random.uniform(15, 30), 1)
    
    # 推奨サイズ（フレーム幅の±10％）
    face_width_min = round(frame_width * 0.9, 1)
    face_width_max = round(frame_width * 1.1, 1)
    
    # 推奨鼻高さ
    nose_height_min = round(random.uniform(10, 15), 1)
    nose_height_max = round(random.uniform(20, 25), 1)
    
    # ランダムな値の選択
    brand = random.choice(brands)
    style = random.choice(styles)
    shape = random.choice(shapes)
    material = random.choice(materials)
    color = random.choice(colors)
    personal_color = random.choice(personal_colors)
    
    # ランダムな顔の形（1-3つ選択）
    num_face_shapes = random.randint(1, 3)
    selected_face_shapes = random.sample(face_shapes, num_face_shapes)
    
    # ランダムなスタイルタグ（1-3つ選択）
    num_style_tags = random.randint(1, 3)
    selected_style_tags = random.sample(styles, num_style_tags)
    
    # 画像URL（サンプル）
    image_urls = [
        f"https://example.com/frames/{id_num}/front.jpg",
        f"https://example.com/frames/{id_num}/side.jpg",
        f"https://example.com/frames/{id_num}/angle.jpg"
    ]
    
    # 価格（7,000円〜30,000円）
    price = random.randint(7, 30) * 1000
    
    # 商品名の生成
    name = f"{brand} {style} {shape}"
    
    # 現在時刻を設定
    current_time = datetime.now()
    
    return {
        "name": name,
        "brand": brand,
        "price": price,
        "style": style,
        "shape": shape,
        "material": material,
        "color": color,
        "frame_width": frame_width,
        "lens_width": lens_width,
        "bridge_width": bridge_width,
        "temple_length": temple_length,
        "lens_height": lens_height,
        "weight": weight,
        "recommended_face_width_min": face_width_min,
        "recommended_face_width_max": face_width_max,
        "recommended_nose_height_min": nose_height_min,
        "recommended_nose_height_max": nose_height_max,
        "personal_color_season": personal_color,
        "face_shape_types": selected_face_shapes,
        "style_tags": selected_style_tags,
        "image_urls": image_urls,
        "created_at": current_time,
        "updated_at": current_time
    }

def main():
    # データベース接続
    Base.metadata.create_all(bind=engine)
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = Session()
    
    try:
        # 既存のフレームデータを確認
        existing_count = db.query(Frame).count()
        print(f"既存のフレームデータ数: {existing_count}")
        
        if existing_count >= 100:
            print("既に十分なデータが存在します。処理をスキップします。")
            return
        
        # 必要な追加データ数
        needed_count = 100 - existing_count
        print(f"追加で {needed_count} 件のダミーデータを生成します。")
        
        # ダミーデータの生成と挿入
        frames_data = []
        for i in range(needed_count):
            frame_data = generate_random_frame(existing_count + i + 1)
            frames_data.append(frame_data)
            
            # データベース用にcreated_atとupdated_atのみを保持した辞書を作成
            db_frame_data = frame_data.copy()
            
            # フレームをデータベースに追加
            db_frame = Frame(**db_frame_data)
            db.add(db_frame)
            
            if (i + 1) % 10 == 0:
                # 10件ごとにコミット
                db.commit()
                print(f"{i + 1} 件のデータを生成しました。")
        
        # 最後のコミット
        if needed_count % 10 != 0:
            db.commit()
        
        print(f"合計 {needed_count} 件のダミーフレームデータを追加しました。")
        
        # JSONファイルにも保存
        with open("dummy_frames.json", "w", encoding="utf-8") as f:
            json.dump(frames_data, f, ensure_ascii=False, indent=2, cls=DateTimeEncoder)
        print("ダミーデータをJSONファイルに保存しました: dummy_frames.json")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main() 