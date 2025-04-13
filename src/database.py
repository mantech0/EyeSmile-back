from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv
import pymysql
import logging
import traceback
from urllib.parse import quote_plus
import time
from pathlib import Path

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
    
    # SQLiteフォールバックフラグを設定
    os.environ['SQLITE_FALLBACK'] = 'true'
    
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

# 環境変数から接続情報を取得
def get_db_connection_string():
    """データベース接続文字列を取得"""
    try:
        # MySQLの接続情報
        db_host = os.environ.get("DB_HOST")
        db_user = os.environ.get("DB_USER")
        db_password = os.environ.get("DB_PASSWORD")
        db_name = os.environ.get("DB_NAME")
        
        logger.info(f"DB接続情報: HOST={db_host}, USER={db_user}, DB={db_name}")
        
        # MySQLの接続情報がすべて揃っている場合
        if all([db_host, db_user, db_password, db_name]):
            # Azure向けの対応: ユーザー名にサーバー名が含まれていない場合は追加
            if db_host and "@" not in db_user and "localhost" not in db_host and "127.0.0.1" not in db_host:
                logger.info(f"Azure MySQL用にユーザー名を修正: {db_user}@{db_host.split('.')[0]}")
                db_user = f"{db_user}@{db_host.split('.')[0]}"
            
            # MySQLの接続文字列を生成
            encoded_password = quote_plus(db_password)
            connection_string = f"mysql+pymysql://{db_user}:{encoded_password}@{db_host}/{db_name}?charset=utf8mb4"
            logger.info("MySQLデータベース接続文字列を生成しました")
            return connection_string
        
        # 接続情報が不足している場合はSQLiteにフォールバック
        logger.warning("MySQL接続情報が不足しています。SQLiteにフォールバックします")
        return None
    except Exception as e:
        logger.error(f"DB接続文字列生成エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return None

def get_db_path():
    """SQLiteデータベースファイルのパスを取得"""
    # 環境変数からSQLiteパスを取得
    sqlite_path = os.environ.get("SQLITE_PATH", "test.db")
    logger.info(f"SQLiteパス: {sqlite_path}")
    
    # 絶対パスに変換
    if not os.path.isabs(sqlite_path):
        sqlite_path = os.path.join(os.getcwd(), sqlite_path)
        logger.info(f"SQLite絶対パス: {sqlite_path}")
    
    return sqlite_path

# データベースエンジンとセッションの作成
def create_db_engine():
    """データベースエンジンを作成"""
    try:
        # 接続文字列の取得を試みる
        connection_string = get_db_connection_string()
        
        # MySQL接続が可能な場合
        if connection_string:
            logger.info("MySQLエンジンを作成します")
            return create_engine(
                connection_string,
                echo=False,
                pool_pre_ping=True,
                pool_recycle=3600,
                connect_args={"connect_timeout": 10}
            )
        
        # SQLiteにフォールバック
        logger.warning("SQLiteエンジンにフォールバックします")
        
        # SQLiteのフォールバックを示す環境変数を設定
        os.environ["SQLITE_FALLBACK"] = "true"
        
        # SQLiteファイルパスの取得
        sqlite_path = get_db_path()
        
        # データベースファイルのディレクトリを確認
        db_dir = os.path.dirname(sqlite_path)
        if db_dir and not os.path.exists(db_dir):
            os.makedirs(db_dir, exist_ok=True)
            logger.info(f"SQLiteディレクトリを作成しました: {db_dir}")
        
        # SQLiteエンジンの作成
        sqlite_url = f"sqlite:///{sqlite_path}"
        logger.info(f"SQLite URL: {sqlite_url}")
        return create_engine(sqlite_url, echo=False, connect_args={"check_same_thread": False})
    
    except Exception as e:
        logger.error(f"データベースエンジン作成エラー: {str(e)}")
        logger.error(traceback.format_exc())
        
        # 最終的なフォールバック: メモリ内SQLite
        logger.warning("メモリ内SQLiteエンジンを作成します")
        return create_engine("sqlite:///:memory:", echo=False, connect_args={"check_same_thread": False})

# MySQLへの接続確認
def check_mysql_connection():
    """MySQLへの接続を確認する"""
    connection_string = get_db_connection_string()
    if not connection_string:
        logger.warning("MySQLの接続情報が不足しています")
        return False
    
    try:
        logger.info("MySQLへの接続確認を開始")
        # 一時的なエンジンを作成して接続テスト
        test_engine = create_engine(
            connection_string,
            echo=False,
            pool_pre_ping=True,
            connect_args={"connect_timeout": 5}
        )
        
        # 接続テスト
        with test_engine.connect() as connection:
            result = connection.execute("SELECT 1")
            logger.info("MySQLへの接続が成功しました")
            return True
    except Exception as e:
        logger.error(f"MySQLへの接続エラー: {str(e)}")
        logger.error(traceback.format_exc())
        return False

# データベースエンジンの作成
engine = create_db_engine()

# セッションの作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# モデルのベースクラス
Base = declarative_base()

# データベースセッションの依存関係
def get_db():
    """APIリクエスト処理のためのデータベースセッションを提供"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 

# テーブル生成
def generate_tables_for_sqlite():
    """SQLiteデータベース用のテーブルを生成する"""
    if os.environ.get("SQLITE_FALLBACK", "false").lower() == "true":
        try:
            logger.info("SQLiteテーブルの生成を開始")
            Base.metadata.create_all(bind=engine)
            logger.info("SQLiteテーブルの生成が完了しました")
            return True
        except Exception as e:
            logger.error(f"SQLiteテーブル生成エラー: {str(e)}")
            logger.error(traceback.format_exc())
            return False
    return False
