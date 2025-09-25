import random
import string
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import paho.mqtt.client as mqtt
import json
from typing import Any
from common import Log, LogLevel
import os

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

MAC_TABLE_PATH = "mac_table.json"
BROKER = "localhost"

nodes = {}
logs = []

def on_message(client, userdata, msg):
    topic = msg.topic
    payload = msg.payload.decode()
    if topic.endswith("/status"):
        data = json.loads(payload)
        nodes[data['uid']] = data
    elif topic.endswith("/log"):
        try:
            log = json.loads(payload)
            logs.append(log)
            if len(logs) > 1000:
                logs.pop(0)
        except json.JSONDecodeError as e: 
            print("Error parsing log message:", e)


mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect(BROKER, 1883)
mqtt_client.subscribe("node/+/status")
mqtt_client.subscribe("node/+/log")
mqtt_client.loop_start()

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

@app.get("/api/nodes")
async def get_nodes() -> list[dict[str, Any]]:
    return list(nodes.values())

@app.get("/api/logs")
async def get_logs() -> list[dict[str, str]]:
    print("Fetching logs, total:", len(logs), "last one is:", logs[-1] if logs else "none")
    return logs[-100:]  # last 100 log messages


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
