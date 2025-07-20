import pymysql
import os
import time

# 接続試行回数
MAX_RETRIES = 2
RETRY_DELAY = 3  # 秒

# 異なるユーザー名形式で試行
user_formats = [
    'TeamEyeSmail',                                   # 基本形式
    'TeamEyeSmail@tech0-gen-8-step4-eyesmile-db-1',  # 完全修飾名
    'TeamEyeSmail@tech0-gen-8-step4-eyesmile-db-1.mysql.database.azure.com'  # FQDN形式
]

for retry in range(MAX_RETRIES):
    for user_format in user_formats:
        try:
            # Azure MySQL接続情報
            db_config = {
                'host': 'tech0-gen-8-step4-eyesmile-db-1.mysql.database.azure.com',
                'user': user_format,
                'password': 'GCmuMMLr0u',
                'database': 'eyesmile',
                'port': 3306,
                'ssl_disabled': False,  # SSLを有効化
                'ssl': {'ca': None},    # CA証明書なし
                'connect_timeout': 10
            }
            
            print(f"試行 {retry+1}/{MAX_RETRIES}, ユーザー形式: {user_format}")
            print("Azure MySQLへの接続を試みています...")
            
            # 接続
            conn = pymysql.connect(**db_config)
            cursor = conn.cursor()
            
            print("接続成功！データベース情報を取得中...")
            
            # テーブル一覧を取得
            print("\n--- テーブル一覧 ---")
            cursor.execute('SHOW TABLES')
            tables = cursor.fetchall()
            for table in tables:
                print(f"テーブル: {table[0]}")
            
            # framesテーブルが存在するか確認
            cursor.execute("SHOW TABLES LIKE 'frames'")
            if cursor.fetchone():
                # フレーム数の確認
                cursor.execute('SELECT COUNT(*) FROM frames')
                count = cursor.fetchone()[0]
                print(f"\nAzure MySQLに接続成功！フレーム数: {count}")
                
                # テーブル構造を確認
                print("\n--- framesテーブルの構造 ---")
                cursor.execute('DESCRIBE frames')
                columns = cursor.fetchall()
                for column in columns:
                    print(f"カラム: {column[0]}, タイプ: {column[1]}")
                
                # サンプルデータを取得
                print("\n--- サンプルデータ ---")
                cursor.execute('SELECT * FROM frames LIMIT 1')
                sample = cursor.fetchone()
                if sample:
                    field_names = [i[0] for i in cursor.description]
                    print("カラム名:", field_names)
                    print("データ例:", sample)
            else:
                print("\nframesテーブルが見つかりませんでした")
            
            # 接続クローズ
            cursor.close()
            conn.close()
            print("\n接続テスト完了")
            
            # 成功したらループを抜ける
            exit(0)
            
        except Exception as e:
            print(f"\n接続エラー: {e}")
            print(f"ユーザー: {user_format}")
            
            # 最後の試行でなければ少し待機
            if retry < MAX_RETRIES - 1 or user_format != user_formats[-1]:
                print(f"{RETRY_DELAY}秒後に再試行します...\n")
                time.sleep(RETRY_DELAY)

# すべての試行が失敗した場合
print("\nすべての接続試行が失敗しました。")
print("\nトラブルシューティング:")
print("1. Azure MySQLサーバーが起動しているか確認")
print("2. ファイアウォール設定でIPアドレスが許可されているか確認")
print("3. ユーザー名とパスワードが正しいか確認")
print("4. データベース名が正しいか確認")
print("5. Azure管理者に問い合わせて権限を確認") 