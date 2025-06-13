import aiohttp
from bs4 import BeautifulSoup
import validators
import urllib.robotparser as robotparser
from urllib.parse import urlparse
import hashlib
import os
from urllib.parse import urljoin
from database_manager import is_url_seen, mark_url_as_seen
import re

def sanitize_filename(name):
    """Loại bỏ ký tự không hợp lệ khỏi tên file."""
    return re.sub(r'[<>:"/\\|?*]', '_', name)

def hard_disk_store(text, url):
    """Lưu nội dung HTML vào file trong thư mục storage với tên dựa trên thẻ <title>."""
    storage_dir = "storage"
    os.makedirs(storage_dir, exist_ok=True)

    # Phân tích HTML để lấy thẻ <title>
    soup = BeautifulSoup(text, "html.parser")
    title = soup.title.string if soup.title else "untitled"
    sanitized_title = sanitize_filename(title)[:100]  # Giới hạn độ dài tên

    # Thêm hash của URL để tránh trùng lặp
    filename = f"{sanitized_title}_{hashlib.md5(url.encode()).hexdigest()}.html"
    filepath = os.path.join(storage_dir, filename)

    if os.path.exists(filepath):
        print(f"File {filename} already exists, skipping...")
        return

    print("HTML stored in:", filepath)

    with open(filepath, "w+", encoding="utf-8") as file:
        file.write(text)

def validate_url(url):
	try:
		if validators.url(url):
			return True
		return False
	except:
		return False

def can_fetch_url(url):
    """
    Kiểm tra URL có được phép crawl hay không dựa vào file robots.txt.
    """
    parsed_url = urlparse(url)
    base_url = f"{parsed_url.scheme}://{parsed_url.netloc}"
    robots_url = f"{base_url}/robots.txt"

    rp = robotparser.RobotFileParser()
    rp.set_url(robots_url)
    try:
        rp.read()
    except Exception as e:
        print(f"Không thể đọc {robots_url}. Mặc định cho phép: {e}")
        return True  # Mặc định cho phép nếu không thể đọc file robots.txt

    user_agent = "trahabo"  # Tên user-agent của crawler (đặt tên riêng của bạn)
    return rp.can_fetch(user_agent, url)

async def crawl(url):
    # Kiểm tra nếu URL đã được crawl
    if is_url_seen(url):
        print(f"URL {url} already seen, skipping...")
        return []

    # Đánh dấu URL đã được xử lý
    mark_url_as_seen(url)
    
    if not can_fetch_url(url):
        print(f"URL {url} is disallowed by robots.txt")
        return []

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=5) as response:
                html = await response.text()
                hard_disk_store(html, url)  # Lưu dữ liệu vào ổ đĩa
                print(f"Crawled URL: {url}")

                # Phân tích HTML để lấy child URLs
                # Lấy các URL từ tag <a>
                soup = BeautifulSoup(html, "html.parser")
                a_urls = [
                    urljoin(url, link.get('href'))
                    for link in soup.find_all('a') if link.get('href')
                ]
                
                # Lấy các URL từ tag <link>
                link_urls = [
                    urljoin(url, link.get('href'))
                    for link in soup.find_all('link') if link.get('href')
                ]
                child_urls = a_urls + link_urls
                return child_urls
    except Exception as e:
        print(f"Error crawling {url}: {e}")
        return []

