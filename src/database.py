from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv
import os
import tempfile
import logging

# ロギングの設定
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# 環境変数をロード
load_dotenv()

# データベース接続情報
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_USER = os.getenv("DB_USER")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME")
DB_SSL_CA = os.getenv("DB_SSL_CA")  # 改行付き証明書（\n含む）

# MySQL接続用URL
SQLALCHEMY_DATABASE_URL = f"mysql+mysqlconnector://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

# PEM形式の証明書を一時ファイルに保存
temp_cert_path = None
if DB_SSL_CA:
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pem", mode="w") as cert_file:
        cert_file.write(DB_SSL_CA.replace("\\n", "\n"))  # \n → 改行に変換
        temp_cert_path = cert_file.name
        logger.info(f"SSL CA certificate written to temp file: {temp_cert_path}")
else:
    logger.warning("DB_SSL_CA not found in .env")

# エンジン作成
connect_args = {}
if temp_cert_path:
    connect_args["ssl_ca"] = temp_cert_path
    connect_args["ssl_verify_cert"] = True

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

# セッションとベースクラス
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# DBセッションを取得する依存関係
def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database error: {e}")
        raise
    finally:
        db.close()