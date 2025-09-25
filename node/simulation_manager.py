import time
from .simulated_node import NodeThread

def main():
    num_nodes = 3  # how many simulated nodes
    threads = []

    for _ in range(num_nodes):
        t = NodeThread()
        t.start()
        threads.append(t)

    # Keep manager alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Simulation manager shutting down...")


if __name__ == "__main__":
    main()
