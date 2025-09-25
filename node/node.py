# node.py
import paho.mqtt.client as mqtt
import json
import time
import socket
import random
from enum import Enum

class LogLevel(Enum):
    DEBUG = "D"
    INFO = "I"
    WARNING = "W"
    ERROR = "E"

class Log:
    def __init__(self, origin: str, message: str, level: LogLevel = LogLevel.INFO):
        self.level = level
        self.message = message
        self.timestamp = time.strftime("%Y-%m-%dT%H:%M:%S")
        self.origin = origin

    def to_dict(self):
        return {
            "timestamp": self.timestamp,
            "origin": self.origin,
            "level": self.level.value,
            "message": self.message,
        }

    def to_json(self):
        return json.dumps(self.to_dict())


class PiNode:
    def __init__(self, uid, name, broker="localhost", heartbeat_interval=2):
        self.uid = uid
        self.name = name
        self.broker = broker
        self.heartbeat_interval = heartbeat_interval
        self.running = False

        self.client = mqtt.Client(client_id=self.uid, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect

        self.status_topic = f"node/{self.uid}/status"
        self.log_topic = f"node/{self.uid}/log"

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            print(f"[{self.uid}] Connected to MQTT broker at {self.broker}")
        else:
            print(f"[{self.uid}] Failed to connect, return code {rc}")

    def get_ip(self):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except:
            return "0.0.0.0"

    def publish_status(self):
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

    def publish_log(self, message, level=LogLevel.INFO):
        log = Log(origin=self.name, message=message, level=level)
        self.client.publish(self.log_topic, log.to_json())
        print(f"[{self.uid}] Log published: {log.to_dict()}")

    def run(self):
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

    def kill(self):
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
