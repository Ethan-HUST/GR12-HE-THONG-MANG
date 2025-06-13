from fastapi import FastAPI, HTTPException
import asyncio
import aiohttp
from pydantic import BaseModel
from crawler import crawl, can_fetch_url  # Hàm crawl bất đồng bộ
from generate_urls import make_urls, get_next_url
import psutil
from pydantic import BaseModel, field_validator, ValidationError
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
import logging

app = FastAPI()

# Biến toàn cục
current_node_index = 0
URLS = []
limiter =  8  # Giới hạn số lượng child URL
child_adjacency = {}
current_tasks = 0

class CrawlRequest(BaseModel):
    website: str
    levels: int

    @field_validator("levels")
    def validate_levels(cls, value):
        if value <= 0:
            raise ValueError("Levels must be greater than 0")
        return value



@app.get("/")
async def root():
    """
    Endpoint mặc định cho root (/) của server.
    """
    return {"message": "Welcome to the distributed crawler node!", "status": "running"}


@app.get("/status")
async def status():
    """
    Route kiểm tra trạng thái node.
    """
    return {
        "status": "healthy",
        "cpu_usage": psutil.cpu_percent(interval=1),
        "memory_usage": psutil.virtual_memory().percent,
        "current_tasks": len(child_adjacency),
    }

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request, exc):
    """
    Ghi đè xử lý lỗi validation, bỏ qua lỗi hoặc trả phản hồi tùy chỉnh.
    """
    # Không log lỗi, chỉ trả về phản hồi mặc định
    logging.info("Validation error occurred but ignored.")
    return JSONResponse(
        status_code=200,
        content={"message": "Validation error ignored."},
    )

@app.post("/crawl")
async def crawl_endpoint(request: CrawlRequest):
    print(f"Received payload: {request.model_dump()}")
    """
    Route xử lý yêu cầu crawl.
    """
    global current_node_index, current_tasks
    try:
        current_tasks +=1
        print(f"Received request: {request.model_dump()}")  # Log payload

        website = request.website
        levels = request.levels

        if not can_fetch_url(website):
            return {"status": "disallowed", "message": f"URL {website} is disallowed by robots.txt"}

        # Crawl URL
        print(f"Crawling website: {website} at levels: {levels}")
        child_urls = await crawl(website)
        print(f"Found child URLs: {child_urls}")

        # Giới hạn số lượng child URLs
        if len(child_urls) > limiter:
            child_urls = child_urls[:limiter]

        # Phân phối child URLs cho các node khác
        tasks = []
        for child_url in child_urls:
            worker_url, current_node_index = get_next_url(URLS, current_node_index)
            tasks.append(send_crawl_request(worker_url, child_url, levels - 1))

        await asyncio.gather(*tasks)

        # Cập nhật adjacency list
        if website not in child_adjacency:
            child_adjacency[website] = child_urls
        else:
            child_adjacency[website] += child_urls

        return {"status": "Crawling completed", "found_urls": child_urls}
    except ValidationError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
    finally:
        current_tasks -= 1
        print(f"Current tasks: {current_tasks}")

@app.get("/make_graph")
async def make_graph(website: str, depth: int):
    """
    Route xử lý tạo đồ thị liên kết.
    """
    print(f"Processing graph for website: {website} at depth: {depth}")

    result = {}
    if website in child_adjacency:
        result[website] = child_adjacency[website][:depth]
    else:
        result[website] = []

    return result


@app.get("/check")
async def check():
    """
    Route kiểm tra trạng thái của các node khác.
    """
    answers = []
    async with aiohttp.ClientSession() as session:
        tasks = [check_node_status(session, url) for url in URLS]
        results = await asyncio.gather(*tasks)
        answers.extend(results)
    return {"status": "Nodes checked", "results": answers}


@app.get("/health")
async def health():
    """
    Route kiểm tra trạng thái node hiện tại.
    """
    return {"host": "localhost", "status": "healthy"}


async def send_crawl_request(worker_url, child_url, levels):
    """
    Gửi yêu cầu crawl không đồng bộ tới các node khác.
    """
    params = {"website": child_url, "levels": levels}
    headers = {"Content-Type": "application/json"}
    print(f"Payload being sent: {params}")
    async with aiohttp.ClientSession(headers=headers) as session:
        try:
            async with session.post(f"{worker_url}crawl", json=params) as response:
                if response.status == 200:
                    print(f"Successfully sent crawl request to {worker_url}")
                else:
                    print(f"Failed to send crawl request to {worker_url} with status {response.status}")
        except Exception as e:
            print(f"Error sending request to {worker_url}: {e}")


async def check_node_status(session, url):
    """
    Kiểm tra trạng thái của một node khác.
    """
    try:
        async with session.get(url + "status", timeout=3) as response:
            return await response.json()
    except Exception as e:
        return {"url": url, "status": "unreachable", "error": str(e)}


if __name__ == "__main__":
    import uvicorn
    import sys
    from generate_urls import make_urls

    try:
        port_number = int(sys.argv[1])
        number_of_nodes = int(sys.argv[2])
    except Exception:
        print("Usage: python node.py <port_number> <number_of_nodes>")
        exit(1)

    # Tạo danh sách URL của các node
    URLS = make_urls(number_of_nodes)

    print(f"Starting server at port {port_number}")
    uvicorn.run(app, host="0.0.0.0", port=port_number)
