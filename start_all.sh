#!/bin/bash
# PiNest startup script
# Starts MQTT broker, activates Python venv, runs FastAPI backend, and frontend dashboard

# --- Start MQTT broker ---
echo "Starting Mosquitto MQTT broker..."
sudo systemctl start mosquitto

# --- Activate Python virtual environment ---
echo "Activating Python virtual environment..."
source ./venv/bin/activate

# --- Run FastAPI backend ---
echo "Starting FastAPI backend..."
# Runs in background
uvicorn backend.dashboard_backend:app --reload --host 0.0.0.0 --port 8000 &
BACKEND_PID=$!

# --- Run Vue frontend ---
echo "Starting Vue frontend..."
cd frontend
npm run dev &
FRONTEND_PID=$!

# --- Cleanup on exit ---
trap "echo 'Stopping servers...'; kill $BACKEND_PID $FRONTEND_PID; deactivate; exit" SIGINT SIGTERM

# --- Wait to keep script alive ---
echo "PiNest services are running. Press Ctrl+C to stop."
wait
