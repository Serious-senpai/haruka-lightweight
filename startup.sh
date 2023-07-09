#!/bin/bash

python3 dummy-server.py &
pid=$!

pip install -r requirements.txt
apt install ffmpeg g++ git -y
g++ -std=c++2a -Wall bot/c++/fuzzy.cpp -o bot/c++/fuzzy.out

kill $pid
python3 bot/main.py
