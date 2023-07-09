#!/bin/bash

python3 dummy-server.py &
pid = $!
pip install --cache-dir pip-cache -r requirements.txt
kill $pid
python3 bot/main.py
