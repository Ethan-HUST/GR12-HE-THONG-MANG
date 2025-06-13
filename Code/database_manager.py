# database_manager.py
import sqlite3

# Tạo kết nối và bảng SQLite
def initialize_db():
    conn = sqlite3.connect('url_seen.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS seen_urls (
            url TEXT PRIMARY KEY
        )
    ''')
    conn.commit()
    conn.close()

# Kiểm tra URL đã được crawl
def is_url_seen(url):
    conn = sqlite3.connect('url_seen.db')
    c = conn.cursor()
    c.execute('SELECT 1 FROM seen_urls WHERE url = ?', (url,))
    result = c.fetchone()
    conn.close()
    return result is not None

# Đánh dấu URL là đã crawl
def mark_url_as_seen(url):
    conn = sqlite3.connect('url_seen.db')
    c = conn.cursor()
    c.execute('INSERT OR IGNORE INTO seen_urls (url) VALUES (?)', (url,))
    conn.commit()
    conn.close()

def clear_seen_urls():
    """
    Xóa toàn bộ dữ liệu trong bảng seen_urls.
    """
    conn = sqlite3.connect('url_seen.db')
    c = conn.cursor()
    c.execute('DELETE FROM seen_urls')
    conn.commit()
    conn.close()
    print("Database cleared: all URLs removed.")