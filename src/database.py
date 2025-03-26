from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pymysql
import logging
import traceback

# ロギングの設定
logger = logging.getLogger(__name__)

load_dotenv()

# データベース接続URLの構築
try:
    # Azure環境の検出
    is_azure = os.getenv('WEBSITE_SITE_NAME') is not None
    logger.info(f"データベース初期化 - 実行環境: {'Azure' if is_azure else 'ローカル'}")
    
    # Azure MySQL接続文字列の構築
    db_user = os.getenv('DB_USER')
    db_password = os.getenv('DB_PASSWORD')
    db_host = os.getenv('DB_HOST')
    db_port = os.getenv('DB_PORT')
    db_name = os.getenv('DB_NAME')
    
    # 完全修飾ユーザー名が設定されていなければ自動的に生成
    if db_user and db_host and '@' not in db_user and '.mysql.database.azure.com' in db_host:
        server_name = db_host.split('.')[0]
        logger.info(f"完全修飾ユーザー名に変換します: {db_user}@{server_name}")
        db_user = f"{db_user}@{server_name}"
    
    logger.info(f"データベース接続情報: host={db_host}, port={db_port}, user={db_user}, database={db_name}")
    
    # 接続URL構築
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    
    # Azureでの接続設定
    if is_azure:
        # Azureでは非常に軽量な設定を使用
        engine_params = {
            "connect_args": {"ssl": True},
            "pool_recycle": 280,
            "pool_size": 1,  # ワーカー数に合わせて最小限に
            "max_overflow": 2,
            "echo": False  # SQLログを無効化（パフォーマンス向上）
        }
        logger.info("Azure環境用の軽量データベース設定を使用")
    else:
        # ローカル開発環境での設定
        engine_params = {
            "connect_args": {"ssl": {"ca": None}},
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "echo": True  # SQLログを出力（デバッグ用）
        }
        logger.info("ローカル環境用のデータベース設定を使用")
    
    logger.info("データベースエンジンを作成しています...")
    engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_params)
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.info("データベース設定が完了しました")
    
except Exception as e:
    logger.error(f"データベース接続設定エラー: {str(e)}")
    logger.error(f"詳細: {e}", exc_info=True)
    
    # フォールバック：エラー時でもアプリケーションが起動できるよう、最小限の設定を用意
    logger.warning("フォールバック設定でデータベース接続を構成します")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.warning("フォールバック設定（SQLite）でデータベース接続を構成しました")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"データベースセッション使用中のエラー: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()
