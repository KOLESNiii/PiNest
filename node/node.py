# node.py
import paho.mqtt.client as mqtt
import json
import time
import socket
import random
from enum import Enum
import uuid
import requests
from typing import Any
from common import Log, LogLevel

TESTING = True # Set to False in production

class PiNode:
    def __init__(self, broker: str = "localhost", backend: str = "http://localhost:8000", heartbeat_interval: int = 2):
        self.uid = self.get_mac() if not TESTING else uuid.uuid4().hex[:8]
        self.broker = broker
        self.backend = backend
        self.heartbeat_interval = heartbeat_interval
        self.running = False

        self.client = mqtt.Client(client_id=self.uid, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect

        self.status_topic = f"node/{self.uid}/status"
        self.log_topic = f"node/{self.uid}/log"

    def on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            print(f"[{self.uid}] Connected to MQTT broker at {self.broker}")
        else:
            print(f"[{self.uid}] Failed to connect, return code {rc}")

    def get_ip(self) -> str:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"
        
    def get_mac(self) -> str:
        mac_num = hex(uuid.getnode()).replace('0x', '').upper()
        mac = ':'.join(mac_num[i:i+2] for i in range(0, 11, 2))
        return mac
    
    def register_with_backend(self) -> dict[str, str]:
        try:
            res = requests.post(f"{self.backend}/api/register", json={"uid": self.uid})
            res.raise_for_status()
            return res.json()
        except Exception as e:
            print(f"[{self.uid}] Failed to register with backend: {e}")
            return {"name": f"temp-{random.randint(1000,9999)}",}

    def publish_status(self) -> None:
        status = {
            "uid": self.uid,
            "name": self.name,
            "ip": self.get_ip(),
            "cpu": round(random.uniform(5, 30), 1),
            "temp": round(random.uniform(40, 60), 1),
            "status": "online",
            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.client.publish(self.status_topic, json.dumps(status))
        print(f"[{self.uid}] Status published: {status}")

    def publish_log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        log = Log(origin=self.name, message=message, level=level)
        self.client.publish(self.log_topic, log.to_json())
        print(f"[{self.uid}] Log published: {log.to_dict()}")

    def run(self) -> None:
        identity = self.register_with_backend()
        self.name = identity["name"]

        self.client.connect(self.broker, 1883, 60)
        self.client.loop_start()
        self.running = True

        try:
            while self.running:
                self.publish_status()
                self.publish_log("Heartbeat check", LogLevel.INFO)
                time.sleep(self.heartbeat_interval)
        except KeyboardInterrupt:
            print(f"[{self.uid}] Shutting down simulated node...")
            self.kill()

    def kill(self) -> None:
        if not self.running:
            return
        
        print(f"[{self.uid}] Shutting down node...")
        self.publish_log("Node recieved shutdown command", LogLevel.INFO)
        self.publish_log("Node shutting down", LogLevel.WARNING)

        offline_status = {
            "uid": self.uid,
            "name": self.name,
            "ip": self.get_ip(),
            "cpu": 0,
            "temp": 0,
            "status": "offline",
            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.client.publish(self.status_topic, json.dumps(offline_status))

        self.running = False
        self.client.loop_stop()
        self.client.disconnect()
        print(f"[{self.uid}] Disconnected from MQTT broker.")

def main() -> None:
    server_ip = "10.0.0.50"
    node = PiNode(broker=server_ip, backend=f"http://{server_ip}:8000")
    try:
        node.run()
    except KeyboardInterrupt:
        node.kill()

if __name__ == "__main__":
    main()
