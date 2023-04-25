import os

import discord


COMMAND_PREFIX = "$"
OWNER_ID = 618361466248232960


INTENTS = discord.Intents.default()
INTENTS.message_content = True
INTENTS.auto_moderation = INTENTS.typing = False


PORT = int(os.environ["PORT"])


BASH_PATH = "./bash.txt"
EVAL_PATH = "./eval.txt"
LOG_PATH = "./log.txt"
FUZZY_MATCH = "./bot/c++/fuzzy.out"


EVAL_TASK_ATTR = "eval_task"


# Required
TOKEN = os.environ["TOKEN"]


# Optional
TOKEN1 = os.environ["TOKEN1"]
