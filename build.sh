#!/usr/bin/env bash
# Exit on error to prevent broken deployments
set -o errexit

echo "--- Starting build process ---"

# 1. Install all Python dependencies from requirements.txt
echo "Installing Python packages..."
pip install -r requirements.txt

# 2. Install the Google AI Gemini CLI
# This command downloads the official installer and runs it.
echo "Installing Gemini CLI..."
curl -o install.sh https://ai.google.dev/gemini-api/install.sh
bash install.sh

echo "Build script finished successfully."