#!/usr/bin/env bash

echo "📥 Installing Google Chrome..."

# Download & install Chrome
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
apt install -y ./google-chrome-stable_current_amd64.deb
rm google-chrome-stable_current_amd64.deb

echo "✅ Google Chrome installed successfully."