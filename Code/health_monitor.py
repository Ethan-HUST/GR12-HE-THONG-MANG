import asyncio
import aiohttp
import subprocess
from datetime import datetime
from generate_urls import make_urls


async def check_node_health(session, url):
    """
    Gửi yêu cầu kiểm tra trạng thái của một node.
    """
    try:
        async with session.get(url + "status", timeout=5) as response:
            if response.status == 200:
                data = await response.json()
                return {"url": url, "status": "healthy", "details": data}
    except Exception as e:
        print(f"[{datetime.now()}] Failed to reach {url}: {e}")
    return {"url": url, "status": "unreachable", "details": None}


async def retry_node(node_index, total_nodes):
    """
    Thử khởi động lại node không phản hồi.
    """
    port = 5000 + node_index
    try:
        print(f"[{datetime.now()}] Restarting node on port {port}...")
        subprocess.Popen(['python', 'node.py', str(port), str(total_nodes)], shell=True)
        await asyncio.sleep(5)  # Chờ node khởi động
        print(f"[{datetime.now()}] Node on port {port} restarted successfully.")
    except Exception as e:
        print(f"[{datetime.now()}] Failed to restart node on port {port}: {e}")


async def periodic_healthcheck(node_count):
    """
    Kiểm tra định kỳ trạng thái của các node.
    """
    urls = make_urls(node_count)
    while True:
        print(f"[{datetime.now()}] Checking node statuses...")
        async with aiohttp.ClientSession() as session:
            tasks = [check_node_health(session, url) for url in urls]
            results = await asyncio.gather(*tasks)

        unreachable_nodes = []
        for result in results:
            if result["status"] == "healthy":
                print(f"[{datetime.now()}] Node {result['url']} is healthy. Details: {result['details']}")
            else:
                print(f"[{datetime.now()}] Node {result['url']} is unreachable.")
                unreachable_nodes.append(urls.index(result["url"]))

        #Xử lý các node không hoạt động
        for node_index in unreachable_nodes:
            await retry_node(node_index, node_count)

        print(f"[{datetime.now()}] Health check completed. Waiting for next round...")
        await asyncio.sleep(10)  # Lặp lại sau 10 giây


if __name__ == "__main__":
    import sys
    try:
        node_count = int(sys.argv[1])
        asyncio.run(periodic_healthcheck(node_count))
    except Exception as e:
        print("Usage: python health_monitor.py <node_count>")
        print(f"Error: {e}")
