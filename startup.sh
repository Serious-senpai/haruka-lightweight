#!/bin/bash

echo "startup.sh started"
python3 prepare.py
python3 bot/main.py
