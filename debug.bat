@echo off
cd bot/web
cmd /q /c flutter build web --output ../server/build --web-renderer html 
cd ../..
python bot/main.py
