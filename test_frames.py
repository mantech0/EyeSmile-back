#!/usr/bin/env python3
import sys
import os
import json
import requests
from pprint import pprint

# カレントディレクトリをバックエンドディレクトリに設定
current_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(current_dir)

# バックエンドAPIのベースURL
API_BASE_URL = "http://localhost:8001"

def test_frames_api():
    """フレームデータを取得するAPIをテストする"""
    print("フレームデータの取得テスト中...")
    
    # アプリがSQLiteにフォールバックしていても動作するはず
    response = requests.get(f"{API_BASE_URL}/api/v1/frames")
    
    if response.status_code == 200:
        frames = response.json()
        print(f"取得したフレーム数: {len(frames)}")
        
        if frames:
            print("\n最初のフレームデータ:")
            pprint(frames[0])
            
            # ファイルに保存
            with open("frames_data.json", "w", encoding="utf-8") as f:
                json.dump(frames, f, ensure_ascii=False, indent=2)
            print(f"\nフレームデータを frames_data.json に保存しました")
        else:
            print("フレームデータが見つかりませんでした")
    else:
        print(f"エラー: ステータスコード {response.status_code}")
        print(response.text)
        
        # エンドポイントが存在しない場合、別のアプローチを試す
        try_recommendation_api()

def try_recommendation_api():
    """レコメンデーションAPIをテストする"""
    print("\nレコメンデーションAPIのテスト中...")
    
    # テスト用のリクエストデータ
    request_data = {
        "face_data": {
            "face_width": 140.0,
            "eye_distance": 65.0,
            "cheek_area": 45.0,
            "nose_height": 45.0,
            "temple_position": 82.0
        },
        "style_preference": {
            "personal_color": "冬",
            "preferred_styles": ["クラシック", "ビジネス"],
            "preferred_shapes": ["ラウンド", "スクエア"],
            "preferred_materials": ["チタン"],
            "preferred_colors": ["ブラック", "シルバー"]
        }
    }
    
    # APIリクエスト
    response = requests.post(
        f"{API_BASE_URL}/api/v1/recommendations/glasses", 
        json=request_data,
        headers={"Content-Type": "application/json"}
    )
    
    if response.status_code == 200:
        data = response.json()
        print("レコメンデーションデータ取得成功")
        
        # メインのレコメンドフレーム情報
        primary_frame = data.get("primary_recommendation", {}).get("frame", {})
        print(f"\nメインのレコメンドフレーム: {primary_frame.get('name')} ({primary_frame.get('brand')})")
        
        # 代替レコメンドフレーム情報
        alternative_frames = data.get("alternative_recommendations", [])
        print(f"代替レコメンド数: {len(alternative_frames)}")
        
        # JSON形式で保存
        with open("recommendation_data.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\nレコメンデーションデータを recommendation_data.json に保存しました")
    else:
        print(f"エラー: ステータスコード {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_frames_api() 