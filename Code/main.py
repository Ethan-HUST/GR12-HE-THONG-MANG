import asyncio
import aiohttp
import json
from util import start_all_nodes, start_health_monitor, MAX_PORTS
from generate_urls import make_urls, get_next_url, check_if_exists_and_print_html
from database_manager import initialize_db, clear_seen_urls

current_node_index = 0
URLS = []

async def main():
    global current_node_index, URLS
    initialize_db()
    clear_seen_urls()

    number_of_ports = int(input("Enter number of nodes: "))
    if number_of_ports > MAX_PORTS:
        print("Only", MAX_PORTS, "nodes created")
        URLS.extend(make_urls(MAX_PORTS))
    else:
        URLS.extend(make_urls(number_of_ports))

    if len(URLS) == 0:
        raise Exception("Configuration error")

    print(URLS)

    try:
        start_all_nodes(number_of_ports)
        start_health_monitor(number_of_ports)
    except Exception as e:
        print("Initial node starting failed")
        print(e)
        raise e

    while True:
        command = input("=> Enter Command: ")

        if command == "end":
            break
        elif command == "crawl":
            website = input("Enter Website: ")
            levels = int(input("Enter levels: "))
            random_url, current_node_index = get_next_url(URLS, current_node_index)

            url = random_url + "crawl"
            params = {"website": website, "levels": levels}

            await crawl_website(url, params)
            continue

        elif command == "show_html":
            name = input('EnterFile html:')
            print(name)
            check_if_exists_and_print_html(name)
            continue

        elif command == "exit":
            exit(0)
        else:
            print("Invalid Command. Try Again.")
            continue

async def crawl_website(url, params):
    async with aiohttp.ClientSession() as session:
        try:
            async with session.post(url, json=params) as response:
                if response.status == 200:
                    print("Crawling successful")
                    print(await response.text())
                else:
                    print(f"Server error: {response.status}, {await response.text()}")
        except Exception as e:
            print(f"Error sending request: {e}")

# Chạy chương trình bất đồng bộ
if __name__ == "__main__":
    asyncio.run(main())
