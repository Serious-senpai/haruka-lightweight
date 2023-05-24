import os

import discord


INVITE_URL = r"https://discord.com/api/oauth2/authorize?client_id=848178172536946708&permissions=70643008&scope=bot%20applications.commands"
COMMAND_PREFIX = "$"
OWNER_ID = 618361466248232960


INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.auto_moderation = INTENTS.typing = False


HOST = "https://haruka39.me"
PORT = int(os.environ["PORT"])


BASH_PATH = "./bash.txt"
LOG_PATH = "./log.txt"
FUZZY_MATCH = "./bot/c++/fuzzy.out"


C_EVAL_PATH = "./cppeval.txt"
C_EVAL_BINARY_PATH = "./bot/c++/eval.out"
EVAL_PATH = "./eval.txt"
EVAL_TASK_ATTR = "eval_task"


# Required
TOKEN = os.environ["TOKEN"]


# Optional
TOKEN1 = os.environ["TOKEN1"]
