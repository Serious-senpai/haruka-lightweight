#!/bin/bash

echo "Starting dummy server on port $PORT"
python3 -m http.server $PORT &
pid=$!
echo "Server started"

pip install -r requirements.txt

kill $pid
python3 bot/main.py
