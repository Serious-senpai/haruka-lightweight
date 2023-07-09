#!/bin/bash

pip install aiohttp
python3 dummy-server.py &
pid = $!

pip install -r requirements.txt

kill $pid
python3 bot/main.py
