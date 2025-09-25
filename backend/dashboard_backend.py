from contextlib import asynccontextmanager
from datetime import datetime
import random
import string
from time import time, sleep
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import paho.mqtt.client as mqtt
import json
from typing import Any
from common import Log, LogLevel
import os

MAC_TABLE_PATH = "mac_table.json"
BROKER = "localhost"
SERVER_HEARTBEAT_INTERVAL = 2       # seconds
NODE_OFFLINE_TIMEOUT = 5            # seconds
NODE_REMOVAL_TIMEOUT = 300          # seconds
LOGGING_LEVEL = LogLevel.INFO

nodes = {}
logs = []

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if topic.endswith("/status"):
        data = json.loads(payload)
        uid = data["uid"]
        data['last_seen_ts'] = datetime.strptime(data['last_seen'], "%Y-%m-%dT%H:%M:%S").timestamp()
        nodes[uid] = data
    elif topic.endswith("/log"):
        try:
            log = json.loads(payload)
            logs.append(log)
            while len(logs) > 1000:
                logs.pop(0)
        except json.JSONDecodeError as e: 
            print("Error parsing log message:", e)


mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 1883)
mqtt_client.subscribe("node/+/status")
mqtt_client.subscribe("node/+/log")
mqtt_client.loop_start()
sleep(0.1) # give some time to connect

@asynccontextmanager
async def lifespan(app: FastAPI):
    heartbeat_task = asyncio.create_task(server_heartbeat_loop())
    try:
        yield
    finally:
        # Clean shutdown
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        print("Shutting down backend...")
        mqtt_client.loop_stop()
        mqtt_client.disconnect()
    

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

if os.path.exists(MAC_TABLE_PATH):
    try:
        with open(MAC_TABLE_PATH, "r") as f:
            mac_table = json.load(f)
            if not isinstance(mac_table, dict):
                print(f"Warning: {MAC_TABLE_PATH} is not a dict. Resetting table.")
                log = Log(origin="backend", message=f"{MAC_TABLE_PATH} is not a dict, resetting table", level=LogLevel.WARNING)
                mqtt_client.publish("node/backend/log", log.to_json())
                mac_table = {}
    except (json.JSONDecodeError, ValueError) as e:
        print(f"Warning: Failed to load {MAC_TABLE_PATH} ({e}). Starting with empty table.")
        log = Log(origin="backend", message=f"Failed to load {MAC_TABLE_PATH} ({e}), starting with empty table", level=LogLevel.WARNING)
        mqtt_client.publish("node/backend/log", log.to_json())
        mac_table = {}
else:
    print(f"{MAC_TABLE_PATH} not found, starting with empty table.")
    log = Log(origin="backend", message=f"{MAC_TABLE_PATH} not found, starting with empty table", level=LogLevel.INFO)
    mqtt_client.publish("node/backend/log", log.to_json())
    mac_table = {}

def generate_name() -> str:
    return "Node-" + "".join(random.choices(string.ascii_uppercase, k=3))

def mark_offline_nodes():
    current_time = time()
    to_update, to_remove = [], []
    for uid, data in nodes.items():
        if current_time - data.get('last_seen_ts', 0) > NODE_REMOVAL_TIMEOUT:
            to_remove.append(uid)
        elif current_time - data.get('last_seen_ts', 0) > NODE_OFFLINE_TIMEOUT:
            to_update.append(uid)
    for uid in to_update:
        if nodes[uid]['status'] != 'offline':
            print(f"[Backend] Marking node {uid} as offline")
            log = Log(origin="backend", message=f"Marking node {uid} as offline", level=LogLevel.DEBUG)
            mqtt_client.publish("node/backend/log", log.to_json())
            nodes[uid]['status'] = 'offline'
    for uid in to_remove:
        print(f"[Backend] Removing node {uid} due to inactivity")
        log = Log(origin="backend", message=f"Removing node {uid} due to inactivity", level=LogLevel.WARNING)
        mqtt_client.publish("node/backend/log", log.to_json())
        del nodes[uid]

async def server_heartbeat_loop():
    while True:
        print("[Backend] Sending server heartbeat")
        log = Log(origin="backend", message="Sending server heartbeat", level=LogLevel.DEBUG)
        mqtt_client.publish("node/backend/log", log.to_json())
        mqtt_client.publish("server/heartbeat", json.dumps({"timestamp": time()}))
        mark_offline_nodes()
        await asyncio.sleep(SERVER_HEARTBEAT_INTERVAL)

@app.get("/api/nodes")
async def get_nodes() -> list[dict[str, Any]]:
    return list(nodes.values())

@app.get("/api/logs")
async def get_logs() -> list[dict[str, Any]]:
    level_order = {"D": 0, "I": 1, "W": 2, "E": 3}
    min_level_value = level_order[LOGGING_LEVEL.value]
    
    filtered_logs = [log for log in logs if level_order[log["level"]] >= min_level_value]
    return filtered_logs[-100:]


@app.post("/api/register")
async def register_node(request: Request) -> dict[str, str]:
    data = await request.json()
    mac = data.get("uid")
    log = Log(origin="backend", message=f"Register request from {mac}", level=LogLevel.INFO)
    mqtt_client.publish("node/backend/log", log.to_json())

    if mac in mac_table:
        name = mac_table[mac]
        print(f"[Backend] Recognised {mac}, returning existing name {name}")
        log = Log(origin="backend", message=f"Found {mac} in table, returning {name}", level=LogLevel.INFO)
        mqtt_client.publish("node/backend/log", log.to_json())
    else:
        name = generate_name()
        mac_table[mac] = name

        with open(MAC_TABLE_PATH, "w") as f:
            json.dump(mac_table, f, indent=2)
        print(f"[Backend] New node registered: {mac} -> {name}")
        log = Log(origin="backend", message=f"Did not find {mac} in table, registered {mac} -> {name}", level=LogLevel.INFO)
        mqtt_client.publish("node/backend/log", log.to_json())

    return {"name": name}
