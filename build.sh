#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install FFmpeg
apt-get update -qq && apt-get -y install ffmpeg

# Install Python dependencies
pip install -r requirements.txt

# Create necessary directories
mkdir -p data/uploads
mkdir -p data/outputs
chmod -R 777 data