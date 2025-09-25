import threading
import random
import time
from .node import PiNode

class NodeThread(threading.Thread):
    def __init__(self, broker="localhost", backend="http://localhost:8000"):
        super().__init__()
        self.broker = broker
        self.node = PiNode(broker=broker, backend=backend)
        self.daemon = True  # ensures thread exits when main exits

    def run(self):
        try:
            while True:
                # Random uptime between 5–15s
                uptime = random.randint(5, 15)
                print(f"[{self.node.uid}] Starting node for {uptime}s")
                t = threading.Thread(target=self.node.run)
                t.start()

                time.sleep(uptime)
                self.node.kill()
                t.join()
                print(f"[{self.node.uid}] Node stopped")

                # Random downtime between 5–10s
                downtime = random.randint(5, 10)
                print(f"[{self.node.uid}] Sleeping {downtime}s before restarting")
                time.sleep(downtime)
        except KeyboardInterrupt:
            print(f"[{self.node.uid}] Simulation interrupted, shutting down...")
            self.node.kill()

def main():
    t = NodeThread()
    t.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("Main thread interrupted, shutting down...")

if __name__ == "__main__":
    main()