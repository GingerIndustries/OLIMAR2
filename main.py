from sechat import Bot

import requests

import os
import logging
import sys

from olimar import OLIMAR2

logging.basicConfig(format="[%(name)s] %(levelname)s: %(message)s", stream=sys.stdout, level=logging.INFO)

languages = list(requests.get("https://ato.pxeger.com/languages.json").json().keys())
bot = Bot()
bot.login(os.environ["email"], os.environ["password"])
room = bot.joinRoom(1)
olimar = OLIMAR2(languages, room, logging.getLogger("OLIMAR"))
try:
    while True:
        pass
finally:
    bot.leaveAllRooms(True)