import pymysql

# 接続情報（直接指定）
db_info = {
    'host': 'tech0-gen-8-step4-eyesmile-db-1.mysql.database.azure.com',
    'user': 'TeamEyeSmail',
    'password': 'GCmuMMLr0u',
    'database': 'eyesmile',
    'port': 3306,
    'ssl': {'ca': None},
    'connect_timeout': 10
}

print("接続情報:", db_info)
print("接続を試みています...")

try:
    # 接続
    conn = pymysql.connect(**db_info)
    cursor = conn.cursor()
    
    # 接続テスト
    cursor.execute("SELECT VERSION()")
    version = cursor.fetchone()
    print(f"接続成功！MySQL バージョン: {version[0]}")
    
    # テーブル一覧
    cursor.execute("SHOW TABLES")
    tables = cursor.fetchall()
    print("\nテーブル一覧:")
    for table in tables:
        print(f"- {table[0]}")
    
    # frames テーブル情報
    cursor.execute("SHOW TABLES LIKE 'frames'")
    if cursor.fetchone():
        cursor.execute("SELECT COUNT(*) FROM frames")
        count = cursor.fetchone()[0]
        print(f"\nフレーム数: {count}")
    
    # 接続を閉じる
    cursor.close()
    conn.close()
    print("\n接続テスト完了")
    
except Exception as e:
    print(f"接続エラー: {e}")
    print("\n考えられる原因:")
    print("1. ホスト名が正しくない")
    print("2. ユーザー名が正しくない")
    print("3. パスワードが正しくない")
    print("4. ファイアウォール設定によりIPアドレスがブロックされている")
    print("5. SSL証明書が必要") 