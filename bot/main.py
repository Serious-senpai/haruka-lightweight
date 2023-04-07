import asyncio
import gc
import logging

from discord.utils import setup_logging

import haruka
from commands import *
from environment import TOKEN
from shared import interface


gc.enable()
setup_logging(
    handler=logging.StreamHandler(stream=interface.logfile),
    formatter=logging.Formatter("[{levelname}] {name}: {message}", style="{"),
    level=logging.INFO,
)

tokens = [TOKEN]
bots = [haruka.Haruka(token=token) for token in tokens]

futures = [interface.start()]
for bot in bots:
    bot.import_commands()
    bot.import_slash_commands()
    futures.append(bot.start())


loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
try:
    loop.run_until_complete(asyncio.gather(*futures))
except KeyboardInterrupt:
    pass
finally:
    print("Terminating application")

    loop.run_until_complete(asyncio.gather(*[bot.close() for bot in bots]))

    for task in asyncio.all_tasks(loop):
        task.cancel()

    loop.run_until_complete(loop.shutdown_asyncgens())
    loop.run_until_complete(loop.shutdown_default_executor())

    print("Application finished")
