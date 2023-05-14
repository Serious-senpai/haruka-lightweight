@echo off
cd bot/web
cmd /q /c flutter build web --profile --source-maps --dart-define=Dart2jsOptimization=O0 --output ../server/build
cd ../..
python bot/main.py
