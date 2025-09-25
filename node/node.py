# node.py
import threading
import paho.mqtt.client as mqtt
import json
import time
import socket
import random
import uuid
import requests
from common import Log, LogLevel
import logging

TESTING = True # Set to False in production

class PiNode:
    def __init__(self, 
                 broker: str = "localhost", 
                 backend: str = "http://localhost:8000", 
                 heartbeat_interval: int = 2,
                 server_offline_timeout: int = 6) -> None:
        self.uid = self.get_mac() if not TESTING else uuid.uuid4().hex[:8]
        self.broker = broker
        self.backend = backend
        self.heartbeat_interval = heartbeat_interval
        self.server_offline_timeout = server_offline_timeout
        self.running = False
        self.server_online = True
        self.last_server_heartbeat = time.time()

        self.logger = logging.getLogger(f"PiNode-{self.uid}")
        self.logger.setLevel(logging.DEBUG)

        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s')
        ch.setFormatter(formatter)
        self.logger.addHandler(ch)

        self.client = mqtt.Client(client_id=self.uid, protocol=mqtt.MQTTv311)
        self.client.on_connect = self.on_connect

        self.status_topic = f"node/{self.uid}/status"
        self.log_topic = f"node/{self.uid}/log"
        self.command_topic = f"node/{self.uid}/command"

        self.actions = {
            "rename": (self.rename, 1),
            "shutdown": (self.shutdown, 0),
            "restart": (self.restart, 0),
        }

        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)

    def log(self, message: str, level: LogLevel = LogLevel.INFO):
        # Map LogLevel to logging module
        level_map = {
            LogLevel.DEBUG: logging.DEBUG,
            LogLevel.INFO: logging.INFO,
            LogLevel.WARNING: logging.WARNING,
            LogLevel.ERROR: logging.ERROR,
        }
        
        # Local logging
        self.logger.log(level_map[level], message)

        # Remote logging via MQTT
        log_obj = Log(origin=self.name, message=message, level=level)
        self.client.publish(self.log_topic, log_obj.to_json())

    def on_connect(self, client, userdata, flags, rc) -> None:
        if rc == 0:
            self.log(f"Connected to MQTT broker at {self.broker}", LogLevel.DEBUG)
            self.client.subscribe("server/heartbeat")
            self.client.message_callback_add("server/heartbeat", self.on_server_heartbeat)
            self.client.subscribe(self.command_topic)
            self.client.message_callback_add(self.command_topic, self.on_command)
        else:
            self.log(f"Failed to connect to MQTT broker, return code {rc}", LogLevel.ERROR)

    def on_server_heartbeat(self, client, userdata, msg):
        """Called whenever server heartbeat is received."""
        self.log("Received server heartbeat", LogLevel.DEBUG)

        payload = msg.payload.decode()
        data = json.loads(payload)
        self.last_server_heartbeat = data["timestamp"]
        if not self.server_online:
            self.log("Server heartbeat restored, marking server as online", LogLevel.INFO)
            self.server_online = True

    def on_command(self, client, userdata, msg):
        """Handles commands sent to this node."""
        try:
            payload = json.loads(msg.payload.decode())
            action = payload.get("action")
            args = payload.get("args", [])
            if action in self.actions:
                cmd, reqargs = self.actions.get(action)

                if len(args) != reqargs:
                    self.log(f"Invalid number of arguments for {action}. Expected {reqargs}, got {len(args)}", LogLevel.ERROR)
                    return
                else:
                    self.log(f"Executing command: {action} with args {args}", LogLevel.INFO)
                    cmd(*args)
            else:
                self.log(f"Unknown command received: {action}", LogLevel.WARNING)
                return
            

        except json.JSONDecodeError as e:
            self.log(f"Failed to decode command payload: {e}", LogLevel.ERROR)

    def _heartbeat_monitor(self):
        """Thread that checks server heartbeat and updates server_online flag."""
        while self.running:
            if time.time() - self.last_server_heartbeat > self.server_offline_timeout:
                if self.server_online:
                    self.log("Server heartbeat lost, marking server as offline", LogLevel.WARNING)
                    self.server_online = False
            time.sleep(1)

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
    
    def rename(self, new_name: str) -> None:
        old_name = getattr(self, "name", None)
        self.name = new_name
        self.log(f"Renamed node from {old_name} to {new_name}", LogLevel.INFO)

    def shutdown(self) -> None:
        self.log("Shutdown command received, shutting down node", LogLevel.WARNING)
        self.kill()
    
    def restart(self) -> None:
        self.log("Restart command received, restarting node", LogLevel.WARNING)
        self.kill()
        time.sleep(2)
        self.run()
    
    def register_with_backend(self) -> dict[str, str]:
        try:
            res = requests.post(f"{self.backend}/api/register", json={"uid": self.uid})
            res.raise_for_status()
            return res.json()
        except Exception as e:
            self.log(f"Failed to register with backend: {e}", LogLevel.ERROR)
            return {"name": f"temp-{random.randint(1000,9999)}",}

    def publish_status(self) -> None:
        status = {
            "uid": self.uid,
            "name": self.name,
            "ip": self.get_ip(),
            "cpu": round(random.uniform(5, 30), 1), # TODO: replace with real CPU usage
            "temp": round(random.uniform(40, 60), 1), # TODO: replace with real temperature
            "status": "online",
            "last_seen": time.strftime("%Y-%m-%dT%H:%M:%S")
        }
        self.client.publish(self.status_topic, json.dumps(status))
        print(f"[{self.uid}] Status published: {status}")

    def run(self) -> None:
        identity = self.register_with_backend()
        self.name = identity["name"]

        self.client.connect(self.broker, 1883, 60)
        self.client.loop_start()
        self.running = True

        self.heartbeat_thread = threading.Thread(target=self._heartbeat_monitor, daemon=True)
        self.heartbeat_thread.start()

        try:
            while self.running:
                self.publish_status()
                self.log("Heartbeat check", LogLevel.DEBUG)

                interval = self.heartbeat_interval
                if not self.server_online:
                    interval *= 2  # reduce frequency
                time.sleep(interval)
        except KeyboardInterrupt:
            self.log("Simulation interrupted, shutting down...", LogLevel.WARNING)
            self.kill()

    def kill(self) -> None:
        if not self.running:
            return
        
        self.log("Node received shutdown command", LogLevel.INFO)
        self.log("Node shutting down", LogLevel.WARNING)

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
        self.heartbeat_thread.join()
        self.client.loop_stop()
        self.client.disconnect()
        self.log("Disconnected from MQTT broker", LogLevel.INFO)

def main() -> None:
    server_ip = "10.0.0.50"
    node = PiNode(broker=server_ip, backend=f"http://{server_ip}:8000")
    try:
        node.run()
    except KeyboardInterrupt:
        node.kill()

if __name__ == "__main__":
    main()
