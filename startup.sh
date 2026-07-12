#!/bin/bash
echo "Installing Google Chrome..."

apt-get update
apt-get install -y wget gnupg
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" > /etc/apt/sources.list.d/google-chrome.list
apt-get update
apt-get install -y google-chrome-stable

echo "Chrome installed:"
google-chrome --version

echo "Starting IQATA Dashboard"
python -m streamlit run dashboard/app.py \
--server.port 8000 \
--server.address 0.0.0.0