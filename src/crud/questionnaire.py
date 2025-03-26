from sqlalchemy.orm import Session
from typing import List
from datetime import date
from .. import models, schemas
import logging

# ロガーの設定
logger = logging.getLogger(__name__)

def ensure_test_user_exists(db: Session, user_id: int = 1) -> int:
    """テスト用ユーザーが存在することを確認し、存在しない場合は作成します"""
    try:
        user = db.query(models.User).filter(models.User.id == user_id).first()
        if not user:
            logger.info(f"テスト用ユーザー(ID: {user_id})が存在しないため作成します")
            test_user = models.User(
                id=user_id,
                email="test@example.com",
                gender="other",
                birth_date=date.today()
            )
            db.add(test_user)
            db.commit()
            db.refresh(test_user)
            logger.info(f"テスト用ユーザー(ID: {user_id})を作成しました")
        return user_id
    except Exception as e:
        logger.error(f"ユーザー確認/作成中にエラーが発生しました: {str(e)}")
        return user_id

def ensure_test_data_exists(db: Session):
    """テスト用のマスターデータが存在することを確認し、不足があれば作成します"""
    try:
        # スタイル質問の確認と作成
        questions = db.query(models.StyleQuestion).all()
        if not questions:
            logger.info("スタイル質問が存在しないため、デフォルトの質問を作成します")
            default_questions = [
                models.StyleQuestion(
                    id=1,
                    question_type="scene",
                    question_text="どんなシーンでアイウェアを着用をしたいですか？",
                    display_order=1,
                    multiple_select=True,
                    options=["仕事", "日常生活", "遊び", "スポーツ", "その他"]
                ),
                models.StyleQuestion(
                    id=2,
                    question_type="image",
                    question_text="どのような印象に見られたいですか？",
                    display_order=2,
                    multiple_select=True,
                    options=["知的", "活発", "落ち着き", "若々しく", "クール", "おしゃれ", "かっこよく", "かわいく", "その他"]
                ),
                models.StyleQuestion(
                    id=3,
                    question_type="fashion",
                    question_text="どんな服装を普段しますか？",
                    display_order=3,
                    multiple_select=True,
                    options=["カジュアル", "フォーマル", "スポーティ", "モード", "シンプル", "ストリート", "アウトドア", "その他"]
                ),
                models.StyleQuestion(
                    id=4,
                    question_type="personal_color",
                    question_text="パーソナルカラーは何色ですか？",
                    display_order=4,
                    multiple_select=False,
                    options=["Spring（スプリング）", "Summer（サマー）", "Autumn（オータム）", "Winter（ウィンター）", "わからない"]
                )
            ]
            db.add_all(default_questions)
            db.commit()
            logger.info("デフォルトの質問を作成しました")

        # プリファレンスの確認と作成
        preferences = db.query(models.Preference).all()
        if not preferences:
            logger.info("プリファレンスが存在しないため、デフォルトのプリファレンスを作成します")
            default_preferences = [
                # シーン
                models.Preference(id=1, category="scene", preference_value="work", display_name="仕事"),
                models.Preference(id=2, category="scene", preference_value="daily", display_name="日常生活"),
                models.Preference(id=3, category="scene", preference_value="play", display_name="遊び"),
                models.Preference(id=4, category="scene", preference_value="sports", display_name="スポーツ"),
                models.Preference(id=5, category="scene", preference_value="other", display_name="その他（シーン）"),
                
                # イメージ
                models.Preference(id=11, category="image", preference_value="intellectual", display_name="知的"),
                models.Preference(id=12, category="image", preference_value="active", display_name="活発"),
                models.Preference(id=13, category="image", preference_value="calm", display_name="落ち着き"),
                models.Preference(id=14, category="image", preference_value="young", display_name="若々しく"),
                models.Preference(id=15, category="image", preference_value="cool", display_name="クール"),
                models.Preference(id=16, category="image", preference_value="stylish", display_name="おしゃれ"),
                models.Preference(id=17, category="image", preference_value="handsome", display_name="かっこよく"),
                models.Preference(id=18, category="image", preference_value="cute", display_name="かわいく"),
                models.Preference(id=19, category="image", preference_value="other", display_name="その他（イメージ）"),
                
                # ファッション
                models.Preference(id=20, category="fashion", preference_value="casual", display_name="カジュアル"),
                models.Preference(id=21, category="fashion", preference_value="formal", display_name="フォーマル"),
                models.Preference(id=22, category="fashion", preference_value="sporty", display_name="スポーティ"),
                models.Preference(id=23, category="fashion", preference_value="mode", display_name="モード"),
                models.Preference(id=24, category="fashion", preference_value="simple", display_name="シンプル"),
                models.Preference(id=25, category="fashion", preference_value="street", display_name="ストリート"),
                models.Preference(id=26, category="fashion", preference_value="outdoor", display_name="アウトドア"),
                models.Preference(id=27, category="fashion", preference_value="other", display_name="その他（ファッション）"),
                
                # パーソナルカラー
                models.Preference(id=28, category="personal_color", preference_value="spring", display_name="Spring（スプリング）"),
                models.Preference(id=29, category="personal_color", preference_value="summer", display_name="Summer（サマー）"),
                models.Preference(id=30, category="personal_color", preference_value="autumn", display_name="Autumn（オータム）"),
                models.Preference(id=31, category="personal_color", preference_value="winter", display_name="Winter（ウィンター）"),
                models.Preference(id=32, category="personal_color", preference_value="unknown", display_name="わからない")
            ]
            db.add_all(default_preferences)
            db.commit()
            logger.info("デフォルトのプリファレンスを作成しました")
            
    except Exception as e:
        db.rollback()
        logger.error(f"テストデータ作成中にエラーが発生しました: {str(e)}")

def create_user_responses(
    db: Session,
    user_id: int,
    responses: List[schemas.UserResponseBase]
) -> List[models.UserResponse]:
    # テスト用ユーザーの存在を確認
    user_id = ensure_test_user_exists(db, user_id)
    
    # テスト用のマスターデータを確認
    ensure_test_data_exists(db)
    
    db_responses = []
    
    for response in responses:
        # 各選択肢に対してレコードを作成
        for preference_id in response.selected_preference_ids:
            db_response = models.UserResponse(
                user_id=user_id,
                question_id=response.question_id,
                selected_preference_id=preference_id
            )
            db_responses.append(db_response)
    
    try:
        db.add_all(db_responses)
        db.commit()
        for response in db_responses:
            db.refresh(response)
        return db_responses
    except Exception as e:
        db.rollback()
        logger.error(f"レスポンス保存中にエラーが発生: {str(e)}")
        raise

def get_user_responses(
    db: Session,
    user_id: int
) -> List[models.UserResponse]:
    return db.query(models.UserResponse).filter(
        models.UserResponse.user_id == user_id
    ).all()