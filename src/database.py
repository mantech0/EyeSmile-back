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
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@"
        f"{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
    )
    
    # SSL設定（Azure MySQLには必要）
    ssl_args = {
        "ssl": {
            "ssl": True,
            "ssl_verify_cert": False,
            "ssl_verify_identity": False
        }
    }
    
    logger.info(f"データベース接続URL: {SQLALCHEMY_DATABASE_URL} (パスワードは非表示)")
    
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL,
        connect_args=ssl_args,
        pool_size=5,
        max_overflow=10,
        pool_timeout=30,
        pool_recycle=1800
    )
    
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    Base = declarative_base()
    
except Exception as e:
    logger.error(f"データベース接続設定エラー: {e}")
    # フォールバック：エラー時でもアプリケーションが起動できるよう、最小限の設定を用意
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    logger.warning("フォールバック設定でデータベース接続を構成しました")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
