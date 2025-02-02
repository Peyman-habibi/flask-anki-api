#!/usr/bin/env bash

echo "📥 Installing required dependencies..."

# Update package lists
apt-get update -y

# Install Chrome dependencies
apt-get install -y wget unzip curl gnupg

echo "📥 Downloading Google Chrome..."
curl -fsSL https://dl.google.com/linux/linux_signing_key.pub | apt-key add -
echo 'deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main' | tee /etc/apt/sources.list.d/google-chrome.list
apt-get update -y
apt-get install -y google-chrome-stable

echo "✅ Google Chrome installed successfully."
