import pandas as pd
from typing import Dict, Any, List

def convert_frame_data(csv_data: Dict[str, Any]) -> Dict[str, Any]:
    """CSVデータをFrameモデルのフォーマットに変換します"""
    
    # スタイルタグの設定
    style_tags = []
    if csv_data['lens_shape_name']:
        style_tags.append(f"shape:{csv_data['lens_shape_name'].lower()}")
    if csv_data['size_name']:
        style_tags.append(f"size:{csv_data['size_name'].lower()}")

    # 推奨される顔幅の計算
    frame_width_map = {
        'とても狭い': {'min': 120, 'max': 130},
        'やや狭い': {'min': 125, 'max': 135},
        '普通': {'min': 130, 'max': 140},
        'やや広い': {'min': 135, 'max': 145},
        'とても広い': {'min': 140, 'max': 150}
    }
    width_range = frame_width_map.get(csv_data['frame_width'], {'min': 130, 'max': 140})

    # 重量の数値化
    weight = float(csv_data['weight'].replace('g', '')) if isinstance(csv_data['weight'], str) else None

    return {
        'name': csv_data['product_name'],
        'brand': csv_data['model_no'],
        'price': 19800,  # デフォルト価格
        'style': csv_data['lens_shape_name'].lower(),
        'shape': csv_data['lens_shape_name'].lower(),
        'material': 'plastic',  # デフォルト材質
        'color': csv_data['color_name'],
        
        # サイズ情報
        'frame_width': float(csv_data['width_mm']),
        'lens_width': float(csv_data['lens_width']),
        'bridge_width': float(csv_data['bridge_size']),
        'temple_length': float(csv_data['temple_size']),
        'lens_height': float(csv_data['lens_height']),
        'weight': weight if weight else 0.0,

        # 推奨情報
        'recommended_face_width_min': float(width_range['min']),
        'recommended_face_width_max': float(width_range['max']),
        'recommended_nose_height_min': float(csv_data['lens_height']) * 0.8,
        'recommended_nose_height_max': float(csv_data['lens_height']) * 1.2,
        
        # スタイル情報
        'personal_color_season': None,
        'face_shape_types': ['all'],  # デフォルト値
        'style_tags': style_tags,
        
        # 画像情報
        'image_urls': []  # デフォルトは空リスト
    }

def convert_csv_to_frames(file_path: str) -> List[Dict[str, Any]]:
    """CSVファイルを読み込み、Frameモデル用のデータリストに変換します"""
    # CSVファイルの読み込み
    df = pd.read_csv(file_path)
    
    # 各行をFrameモデル形式に変換
    frames = []
    for _, row in df.iterrows():
        try:
            frame_data = convert_frame_data(row)
            frames.append(frame_data)
        except Exception as e:
            print(f"Error converting row: {row['product_name']}, Error: {str(e)}")
            continue
    
    return frames 