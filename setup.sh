#!/bin/bash
# PiNest setup script
# Installs dependencies, sets up venv, installs backend/frontend packages

# --- Update system ---
echo "Updating system..."
sudo apt update && sudo apt upgrade -y

# --- Install system dependencies ---
echo "Installing system dependencies..."
sudo apt install -y python3 python3-venv python3-pip mosquitto mosquitto-clients nodejs npm curl

# --- Create Python virtual environment ---
echo "Creating Python virtual environment..."
python3 -m venv venv

# --- Activate venv ---
echo "Activating venv..."
source ./venv/bin/activate

# --- Install Python dependencies ---
echo "Installing Python packages..."
pip install --upgrade pip
pip install -r requirements.txt

# --- Setup frontend ---
echo "Setting up Vue frontend..."
cd frontend

# Check if package.json exists, else create project
if [ ! -f package.json ]; then
    echo "Initializing Vue project..."
    npm create vite@latest . -- --template vue-ts
fi

npm install

# --- Done ---
echo "Setup complete!"
echo "You can now run './start_all.sh' to start the dashboard, backend, and MQTT broker."
