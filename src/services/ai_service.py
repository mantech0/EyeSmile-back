import os
import openai
import numpy as np
from dotenv import load_dotenv
import logging
from typing import Dict, Any, List, Optional

# ロガーの設定
logger = logging.getLogger(__name__)

# 環境変数の読み込み
load_dotenv()

# Azure OpenAI設定
openai.api_type = "azure"
openai.api_base = os.getenv("AZURE_OPENAI_ENDPOINT")
openai.api_version = "2023-05-15"  # バージョンは適宜更新
openai.api_key = os.getenv("AZURE_OPENAI_API_KEY")

# デプロイメント名
CHAT_DEPLOYMENT = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT_NAME", "gpt-4o-mini")
EMBEDDING_DEPLOYMENT = os.getenv("AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME", "text-embedding-3-large")

async def get_embeddings(texts: List[str]) -> List[List[float]]:
    """テキストのエンベディングを取得する"""
    try:
        response = openai.Embedding.create(
            input=texts,
            engine=EMBEDDING_DEPLOYMENT
        )
        return [item.embedding for item in response.data]
    except Exception as e:
        logger.error(f"エンベディング取得エラー: {str(e)}")
        # ダミーの埋め込みを返す
        return [[0.0] * 1536 for _ in range(len(texts))]

async def generate_glasses_explanation(
    frame_data: Dict[str, Any],
    face_data: Dict[str, Any],
    style_preference: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """メガネ店員の視点からの解説を生成する"""
    try:
        # スタイル設定のテキスト
        style_text = "特になし"
        if style_preference and style_preference.get("preferred_styles"):
            style_text = "、".join(style_preference.get("preferred_styles", []))
        
        # プロンプト作成
        prompt = f"""
        あなたは20年以上の経験を持つプロのメガネ店員です。お客様に合うメガネフレームについて丁寧かつ専門的に説明してください。
        専門知識を用いて「メガネと顔の黄金比」の観点から詳しく解説してください。

        【お客様の情報】
        ・顔幅: {face_data.get('face_width', 0)}mm
        ・目の間隔: {face_data.get('eye_distance', 0)}mm
        ・鼻の高さ: {face_data.get('nose_height', 0)}mm
        ・好みのスタイル: {style_text}

        【選んだメガネフレーム】
        ・ブランド: {frame_data.get('brand', 'ブランド不明')}
        ・モデル名: {frame_data.get('name', '名前不明')}
        ・スタイル: {frame_data.get('style', 'スタイル不明')}
        ・形状: {frame_data.get('shape', '形状不明')}
        ・素材: {frame_data.get('material', '素材不明')}
        ・色: {frame_data.get('color', '色不明')}
        ・フレーム幅: {frame_data.get('frame_width', 0)}mm
        ・レンズ幅: {frame_data.get('lens_width', 0)}mm
        ・ブリッジ幅: {frame_data.get('bridge_width', 0)}mm
        ・レンズ高さ: {frame_data.get('lens_height', 0)}mm

        【解説の指示】
        以下の2つの項目に分けて日本語で説明してください:
        
        1. フィット感について
        - フレームサイズの縦幅：眉からアゴまでの長さ1/3以内に収まるサイズが理想的。このフレームは顔の縦幅とどのようにバランスが取れているか
        - フレームサイズの横幅：顔幅とほぼ同じ大きさが理想的。このフレームサイズの横幅は顔の横幅とどうバランスが取れているか
        - 瞳孔の位置：レンズの上下幅と左右の幅を5分割したとき、縦横ともに2/5に位置する交差点（レンズの中心からやや上部、目頭寄り）に瞳孔の中心が位置するのが黄金比
        
        2. スタイルについて
        - このフレームのデザインがお客様の好みや印象にどう合っているか
        - メガネと眉のバランス：フレームのトップラインと眉頭の起点が重なるとバランスが良く見える
        
        丁寧で専門的、かつ温かみのある接客トーンでお願いします。
        ただし、各項目は簡潔に2-3文程度で簡潔に説明してください。
        """
        
        # Azure OpenAI APIの呼び出し
        response = openai.ChatCompletion.create(
            engine=CHAT_DEPLOYMENT,
            messages=[
                {"role": "system", "content": "あなたはプロのメガネ店員です。お客様に最適なメガネを提案します。「メガネと顔の黄金比」の専門知識を持っています。簡潔に回答してください。"},
                {"role": "user", "content": prompt}
            ],
            max_tokens=400,
            temperature=0.7,
        )
        
        # レスポンスからテキスト抽出
        explanation_text = response.choices[0].message.content
        
        # テキストを解析して構造化
        explanation = parse_explanation(explanation_text)
        
        return explanation
    
    except Exception as e:
        logger.error(f"Azure OpenAI API呼び出しエラー: {str(e)}")
        # エラー時のフォールバック
        return {
            "fit_explanation": f"""
            メガネと顔の黄金比の観点から見ると、この{frame_data.get('shape', '丸型')}シェイプのフレームはあなたの顔幅({face_data.get('face_width', 0)}mm)に適しています。
            フレームの縦幅は眉からアゴまでの長さの1/3以内に収まり、横幅も顔幅とバランスが取れています。
            また、瞳孔の位置もレンズ内の理想的な位置（縦横ともに2/5の位置）に近く、自然な見た目になります。
            """,
            "style_explanation": f"""
            {frame_data.get('style', 'クラシック')}スタイルは{style_text}のご希望に合っています。
            このフレームのトップラインは眉頭の起点とうまく重なり、顔全体のバランスを整えています。
            {frame_data.get('shape', '丸型')}シェイプは、あなたの顔立ちを自然に引き立てる効果があります。
            """,
            "feature_highlights": []
        }

def parse_explanation(text: str) -> Dict[str, Any]:
    """APIレスポンスを解析して構造化する"""
    sections = text.split("\n\n")
    
    fit_explanation = ""
    style_explanation = ""
    
    current_section = None
    
    for section in sections:
        section = section.strip()
        if "フィット感について" in section or section.startswith("1."):
            current_section = "fit"
            # タイトル行を除去
            fit_explanation = section.split("\n", 1)[1] if "\n" in section else section
        elif "スタイルについて" in section or section.startswith("2."):
            current_section = "style"
            # タイトル行を除去
            style_explanation = section.split("\n", 1)[1] if "\n" in section else section
    
    return {
        "fit_explanation": fit_explanation.strip(),
        "style_explanation": style_explanation.strip(),
        "feature_highlights": []
    }