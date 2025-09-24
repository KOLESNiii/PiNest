from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import paho.mqtt.client as mqtt
import json

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

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

@app.get("/api/nodes")
async def get_nodes():
    return list(nodes.values())

@app.get("/api/logs")
async def get_logs():
    print("Fetching logs, total:", len(logs), "last one is:", logs[-1] if logs else "none")
    return logs[-100:]  # last 100 log messages
