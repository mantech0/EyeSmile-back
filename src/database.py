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
    db_port = os.getenv('DB_PORT', '3306')
    db_name = os.getenv('DB_NAME')
    
    # 接続情報のログ
    masked_password = '*' * (len(db_password) if db_password else 0)
    logger.info(f"DB接続情報: USER={db_user}, HOST={db_host}, PORT={db_port}, DB={db_name}, PASS={masked_password[:2] + '***' if masked_password else None}")
    
    # 完全修飾ユーザー名の確認（@がない場合はホスト名を付加）
    if db_user and '@' not in db_user and db_host and '.mysql.database.azure.com' in db_host:
        server_name = db_host.split('.')[0]
        logger.info(f"完全修飾ユーザー名に変換します: {db_user}@{server_name}")
        db_user = f"{db_user}@{server_name}"
    
    # SSL設定（環境変数から取得）
    db_ssl_mode = os.getenv('DB_SSL_MODE', 'require').lower()
    logger.info(f"SSL設定: {db_ssl_mode}")
    
    logger.info(f"データベース接続情報: host={db_host}, port={db_port}, user={db_user}, database={db_name}, ssl_mode={db_ssl_mode}")
    
    # 接続URL構築
    SQLALCHEMY_DATABASE_URL = (
        f"mysql+pymysql://{db_user}:{db_password}@"
        f"{db_host}:{db_port}/{db_name}"
    )
    
    # Azureでの接続設定
    if is_azure:
        # SSL設定はDB_SSL_MODEに基づいて構成
        ssl_config = {}
        if db_ssl_mode in ['require', 'preferred', 'verify-ca', 'verify-full']:
            # Azure MySQLはSSLを要求するため、接続オプションを調整
            ssl_config = {
                "ssl": {
                    "ca": None,  # CA検証なしでも接続可能
                    "check_hostname": False,  # ホスト名検証の無効化（必要に応じて）
                },
                "connect_timeout": 60,  # 接続タイムアウトを60秒に設定
            }
        elif db_ssl_mode == 'disable':
            ssl_config = {"connect_timeout": 60}  # SSL無効、タイムアウトのみ設定
        else:
            # デフォルトは必須（検証なし）
            ssl_config = {
                "ssl": {"ca": None},
                "connect_timeout": 60
            }
        
        logger.info(f"Azure環境用SSL設定: {ssl_config}")
        
        # Azureでの接続設定（SSL設定を変数から取得）
        engine_params = {
            "connect_args": ssl_config,
            "pool_recycle": 280,  # Azureの接続タイムアウト（5分）より小さく設定
            "pool_pre_ping": True,  # 接続前にpingを送信して有効性を確認
            "pool_size": 2,
            "max_overflow": 3,
            "pool_timeout": 60,  # プールからの接続取得タイムアウト
            "echo": True  # デバッグ中はSQLログ出力を有効化
        }
        logger.info(f"Azure環境用のデータベース設定: {engine_params}")
    else:
        # ローカル開発環境での設定
        engine_params = {
            "connect_args": {"ssl": {"ca": None}, "connect_timeout": 30},
            "pool_pre_ping": True,  # 接続前にpingを送信して有効性を確認
            "pool_size": 5,
            "max_overflow": 10,
            "pool_timeout": 30,
            "pool_recycle": 1800,
            "echo": True
        }
        logger.info(f"ローカル環境用のデータベース設定: {engine_params}")
    
    # 最初に接続テストを行う
    logger.info("データベース接続テスト中...")
    connection_success = False
    try:
        test_engine = create_engine(SQLALCHEMY_DATABASE_URL, **engine_params)
        with test_engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info(f"データベース接続テスト成功: {result.fetchone()}")
            connection_success = True
    except Exception as e:
        logger.error(f"データベース接続テスト失敗: {str(e)}")
        logger.error(f"接続URL: {SQLALCHEMY_DATABASE_URL.replace(db_password, '******') if db_password else SQLALCHEMY_DATABASE_URL}")
        logger.error(f"接続パラメータ: {engine_params}")
        
        # Azureでの特定のエラーを詳細にログ出力
        if 'SSL connection error' in str(e):
            logger.error("SSL接続エラー: Azureの設定を確認してください")
        elif 'Access denied' in str(e):
            logger.error("アクセス拒否エラー: ユーザー名とパスワードを確認してください")
        elif 'Unknown MySQL server host' in str(e):
            logger.error("ホスト名解決エラー: データベースホスト名を確認してください")
            
        # エラーがあってもSQLiteでの起動を試みるためここでは例外を再スローしない
    
    # 実際のエンジン設定
    if connection_success:
        logger.info("MySQL接続成功: データベースエンジンを設定します")
        engine = test_engine  # テスト成功したエンジンを使用
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        Base = declarative_base()
        logger.info("データベース設定が完了しました")
    else:
        # 接続に失敗した場合はSQLiteにフォールバック
        raise Exception("MySQL接続に失敗しました。SQLiteにフォールバックします。")
    
except Exception as e:
    logger.error(f"データベース接続設定エラー: {str(e)}")
    logger.error(f"詳細: {e}", exc_info=True)
    
    # フォールバック：エラー時でもアプリケーションが起動できるよう、SQLiteに切り替え
    logger.warning("フォールバック設定でデータベース接続を構成します - SQLiteを使用")
    SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base = declarative_base()
    
    # SQLiteファイルを作成するためにテーブルを生成
    try:
        Base.metadata.create_all(bind=engine)
        logger.warning("SQLiteデータベースファイルとテーブルを作成しました")
    except Exception as e:
        logger.error(f"SQLiteデータベース初期化エラー: {str(e)}")

def get_db():
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"データベースセッション使用中のエラー: {str(e)}")
        logger.error(traceback.format_exc())
    finally:
        db.close()
