pip install -r requirements.txt
apt install ffmpeg g++ -y
g++ -std=c++2a -Wall bot/c++/fuzzy.cpp -o bot/c++/fuzzy.out
python3 bot/main.py
