import socket
import json
import threading
import time

MY_NAME = "A"
MY_PORT = 5001

NEIGHBOURS = {
    "B": (1, 5002),
    "C": (3, 5003),
}

routing_table = {
    "A": [0, "A"],
    "B": [1, "B"],
    "C": [3, "C"],
}

table_lock = threading.Lock()

def print_table():
    print(f"\n Router {MY_NAME} Routing Table:")
    print(f"{'Destination':<15} {'Cost':<10} {'Next Hop'}")
    print("-" * 35)
    with table_lock:
        for dest, (cost, hop) in sorted(routing_table.items()):
            print(f"{dest:<15} {cost:<10} {hop}")
    print()

def send_table_to_neighbours():
    while True:
        time.sleep(3)
        with table_lock:
            data = json.dumps({"from": MY_NAME, "table": routing_table})
        for neighbour, (_, port) in NEIGHBOURS.items():
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.connect(("127.0.0.1", port))
                s.sendall(data.encode())
                s.close()
            except ConnectionRefusedError:
                print(f"Could not reach Router {neighbour} yet...")

def update_table(from_router, received_table):
    cost_to_sender = NEIGHBOURS[from_router][0]
    changed = False
    with table_lock:
        for dest, (their_cost, _) in received_table.items():
            new_cost = cost_to_sender + their_cost
            if dest not in routing_table or new_cost < routing_table[dest][0]:
                routing_table[dest] = [new_cost, from_router]
                changed = True
    if changed:
        print(f"Router {MY_NAME} updated its table after hearing from Router {from_router}")
        print_table()

def listen_for_updates():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(("127.0.0.1", MY_PORT))
    server.listen(5)
    print(f"Router {MY_NAME} is listening on port {MY_PORT} ...")
    while True:
        conn, _ = server.accept()
        raw = conn.recv(4096).decode()
        conn.close()
        msg = json.loads(raw)
        from_router = msg["from"]
        received_table = msg["table"]
        print(f"Router {MY_NAME} received update from Router {from_router}")
        update_table(from_router, received_table)

if __name__ == "__main__":
    print(f"Starting Router {MY_NAME}")
    print_table()
    threading.Thread(target=listen_for_updates, daemon=True).start()
    threading.Thread(target=send_table_to_neighbours, daemon=True).start()
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print(f"Router {MY_NAME} shutting down.")