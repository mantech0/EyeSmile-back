from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pymysql
import logging

# ロギングの設定
logger = logging.getLogger(__name__)

load_dotenv()

# データベース接続URLの構築
try:
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
    
    logger.info(f"Database connection params: host={db_host}, port={db_port}, user={db_user}, database={db_name}")
    
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    
    # Azure MySQL用のSSL設定
    ssl_args = {"ssl": {"ca": None}}
    if os.getenv('DB_SSL_MODE') == 'require':
        logger.info("SSL接続を有効化します")
    
    logger.info(f"データベース接続URL構築完了（パスワードは非表示）")
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=ssl_args,
        echo=True,  # SQLログを出力（デバッグ用）
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base = declarative_base()
    
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
        logger.error(f"データベースセッションエラー: {str(e)}")
        raise
    finally:
        db.close()
