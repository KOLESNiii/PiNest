import paho.mqtt.client as mqtt
import json
import time
import random
import socket
from enum import Enum

# --- Node configuration ---
UID = "test-node-001"       # Unique identifier for this node
NAME = "Test Node"          # Human-friendly name
BROKER = "localhost"        # MQTT broker address
STATUS_TOPIC = f"node/{UID}/status"
LOG_TOPIC = f"node/{UID}/log"
HEARTBEAT_INTERVAL = 2      # seconds between status updates

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

# --- Connect to MQTT broker ---
client = mqtt.Client(client_id=UID, protocol=mqtt.MQTTv311)


def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print(f"[{UID}] Connected to MQTT broker at {BROKER}")
    else:
        print(f"[{UID}] Failed to connect, return code {rc}")

client.on_connect = on_connect
client.connect(BROKER, 1883, 60)
client.loop_start()

# --- Helper function to get fake IP ---
def get_fake_ip():
    # Try to get the local IP of this machine
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "192.168.1.100"

# --- Main loop ---
try:
    while True:
        # Generate fake node status
        status = {
            "uid": UID,
            "name": NAME,
            "ip": get_fake_ip(),
            "cpu": round(random.uniform(5, 30), 1),
            "temp": round(random.uniform(40, 60), 1),
            "status": "online",
            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        client.publish(STATUS_TOPIC, json.dumps(status))
        print(f"[{UID}] Status published: {status}")

        # Publish a fake log entry
        log = Log(origin=NAME, message="Heartbeat check", level=LogLevel.INFO)
        client.publish(LOG_TOPIC, log.to_json())
        print(f"[{UID}] Log published: {log.to_dict()}")

        time.sleep(HEARTBEAT_INTERVAL)

except KeyboardInterrupt:
    print(f"[{UID}] Shutting down simulated node...")
    client.publish(STATUS_TOPIC, json.dumps({
        "uid": UID,
        "name": NAME,
        "ip": get_fake_ip(),
        "cpu": 0,
        "temp": 0,
        "status": "offline",
        "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
    }))
    client.publish(LOG_TOPIC, Log(origin=NAME, message="Node shutting down", level=LogLevel.WARNING).to_json())
    client.loop_stop()
    client.disconnect()
