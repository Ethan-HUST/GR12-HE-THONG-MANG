def make_urls(number_of_ports):
	URLS = []
	for i in range(number_of_ports):
		url = "http://localhost:" + str(5000+i) + "/"
		URLS.append(url)
	return URLS
	URLS = []

# Round Robin implementation
current_node_index = 0  # Biến toàn cục để lưu trạng thái vòng xoay

def get_next_url(list_of_urls, current_node_index):
    url = list_of_urls[current_node_index]
    current_node_index = (current_node_index + 1) % len(list_of_urls)
    return url, current_node_index


def check_if_exists_and_print_html(name):
	try:
		f = open(name, 'r')
		Lines = f.readlines()
		for line in Lines:
			print(line)
		f.close()
	except IOError:
		print("File not accessible")
	return