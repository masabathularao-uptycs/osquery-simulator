#!/bin/bash

# Exit immediately if any command fails
set -e

echo "Stashing any changes..."
git stash

echo "Fetching latest updates from remote..."
git fetch

echo "Checking out requirements.txt from origin/main..."
git checkout origin/main -- requirements.txt

echo "Installing dependencies from requirements.txt..."
pip3 install -r requirements.txt

echo "Pulling latest changes from origin/main..."
git pull origin main

echo "All tasks completed successfully!"
