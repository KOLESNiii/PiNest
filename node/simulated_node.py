import threading
import random
import time
from node import PiNode

class NodeThread(threading.Thread):
    def __init__(self, uid, name, broker="localhost"):
        super().__init__()
        self.uid = uid
        self.name = name
        self.broker = broker
        self.node = PiNode(uid=self.uid, name=self.name, broker=self.broker)
        self.daemon = True  # ensures thread exits when main exits

    def run(self):
        try:
            while True:
                # Random uptime between 5–15s
                uptime = random.randint(5, 15)
                print(f"[{self.uid}] Starting node for {uptime}s")
                t = threading.Thread(target=self.node.run)
                t.start()

                time.sleep(uptime)
                self.node.kill()
                t.join()
                print(f"[{self.uid}] Node stopped")

                # Random downtime between 5–10s
                downtime = random.randint(5, 10)
                print(f"[{self.uid}] Sleeping {downtime}s before restarting")
                time.sleep(downtime)
        except KeyboardInterrupt:
            print(f"[{self.uid}] Simulation interrupted, shutting down...")
            self.node.kill()

def main():
    t = NodeThread(uid="sim-node-001", name="Simulated Node 1")
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main thread interrupted, shutting down...")

if __name__ == "__main__":
    main()