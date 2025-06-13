import subprocess

MAX_PORTS = 6

def start_all_nodes(n):
    for i in range(n):
        port = 5000 + i
        # Use 'start' in cmd to open a new terminal
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'node.py', str(port), str(n)], shell=True)

def start_a_nodes(n, num_nodes):
    port = 5000 + n
    # Run the node script directly
    subprocess.Popen(['start', 'cmd', '/k', 'python', 'node.py', str(port), str(n)], shell=True)


def start_health_monitor(num_nodes):
    subprocess.Popen(['start', 'cmd', '/k', 'python', 'health_monitor.py', str(num_nodes)], shell=True)

def node_retry(tries, node, num_nodes):
    if tries == 0:
        print(f"Node {node} is marked as unreachable after {tries} retries.")
        return

    try:
        port = 5000 + node
        subprocess.Popen(['start', 'cmd', '/k', 'python', 'node.py', str(port), str(num_nodes)], shell=True)
    except Exception as e:
        print(f"Retry failed for node {node}: {e}")
        node_retry(tries - 1, node, num_nodes)

