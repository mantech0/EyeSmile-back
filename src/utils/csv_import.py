import csv
import json
from typing import List, Dict, Any
from datetime import datetime

def validate_frame_data(row: Dict[str, Any]) -> Dict[str, Any]:
    """CSVの行データをバリデーションし、適切な型に変換します"""
    try:
        # 必須フィールドの存在チェック
        required_fields = ['name', 'brand', 'price', 'style', 'shape', 'material', 'color']
        for field in required_fields:
            if not row.get(field):
                raise ValueError(f"必須フィールド '{field}' が空です")

        # 数値フィールドの変換とバリデーション
        numeric_fields = {
            'price': int,
            'frame_width': float,
            'lens_width': float,
            'bridge_width': float,
            'temple_length': float,
            'lens_height': float,
            'weight': float,
            'recommended_face_width_min': float,
            'recommended_face_width_max': float,
            'recommended_nose_height_min': float,
            'recommended_nose_height_max': float
        }

        for field, type_func in numeric_fields.items():
            if row.get(field):
                try:
                    row[field] = type_func(row[field])
                except ValueError:
                    raise ValueError(f"フィールド '{field}' の値が不正です: {row[field]}")

        # JSON形式のフィールドの処理
        json_fields = ['face_shape_types', 'style_tags', 'image_urls']
        for field in json_fields:
            if row.get(field):
                try:
                    if isinstance(row[field], str):
                        row[field] = json.loads(row[field])
                    if not isinstance(row[field], list):
                        row[field] = [row[field]]
                except json.JSONDecodeError:
                    # カンマ区切りの文字列として処理
                    row[field] = [item.strip() for item in row[field].split(',')]

        return row
    except Exception as e:
        raise ValueError(f"データの検証に失敗しました: {str(e)}")

def parse_csv_file(file_path: str) -> List[Dict[str, Any]]:
    """CSVファイルを読み込み、フレームデータのリストを返します"""
    frames = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                validated_row = validate_frame_data(row)
                frames.append(validated_row)
        return frames
    except Exception as e:
        raise Exception(f"CSVファイルの読み込みに失敗しました: {str(e)}") 