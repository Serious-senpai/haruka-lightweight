#!/bin/bash

echo "startup.sh started"
python3 -m http.server $PORT &
pid=$!
echo "Started dummy HTTP server with process $pid"

pip install -r requirements.txt
apt install ffmpeg g++ git -y
g++ -std=c++2a -Wall bot/c++/fuzzy.cpp -o bot/c++/fuzzy.out

echo "Killing process $pid"
kill $pid
wait $pid
python3 bot/main.py
