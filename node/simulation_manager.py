import multiprocessing
import time
from node import PiNode

def run_node(uid, name):
    node = PiNode(uid=uid, name=name)
    node.run()

if __name__ == "__main__":
    processes = []
    num_nodes = 3  # change to simulate more nodes

    for i in range(num_nodes):
        uid = f"sim-node-{i+1:03d}"
        name = f"Simulated Node {i+1}"
        p = multiprocessing.Process(target=run_node, args=(uid, name))
        p.start()
        processes.append(p)
        time.sleep(0.5)  # stagger startup slightly

    try:
        for p in processes:
            p.join()
    except KeyboardInterrupt:
        print("Shutting down simulation...")
        for p in processes:
            p.terminate()
