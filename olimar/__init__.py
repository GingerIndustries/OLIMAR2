from typing import Final

from sechat import Room
from sechat.events import Events
from bs4 import BeautifulSoup

import threading
import re
import logging

from olimar.ato import ATO, Result, StatusType

class OLIMAR2:
    def __init__(self, languages: list[str], room: Room, logger: logging.Logger):
        self.logger: Final[logging.Logger] = logger
        self.ato: Final[ATO] = ATO()
        self.languages: Final[list[str]] = languages
        self.room: Final[Room] = room
        self.room.on(Events.MESSAGE, self.onMessage)
        self.room.on(Events.MENTION, self.onPing)

    def run(self, event, language: str, code: str):
        self.logger.info(f"Running {language} program in message {event.message_id}")
        message = self.room.send(self.room.buildReply(event.message_id, "Processing..."))
        result: Final[Result] = self.ato.run(language, code)
        match result.status.type:
            case StatusType.TIMED_OUT:
                self.logger.info(f"{event.message_id} timed out.")
                self.logger.edit(message, self.room.buildReply(event.user_id, "Timed out."))
                return
            case StatusType.KILLED:
                resultString = "Process was killed."
            case StatusType.CORE_DUMPED:
                resultString = "Process dumped core."
            case StatusType.EXITED:
                resultString = f"Process exited with code {result.status.code}."
            case StatusType.UNKNOWN:
                resultString = "Unknown response. (server on fire?)"
        self.logger.info(f"{event.message_id} succeeded: {result}")
        self.room.edit(message, self.room.buildReply(event.message_id, f"{resultString}\nstdout:\n{result.stdout.decode('utf-8').strip()}\nstderr:\n{result.stderr.decode('utf-8').strip()}"))

    def onMessage(self, event):
        if event.user_id == self.room.userID:
            return
        soup = BeautifulSoup(event.content, 'html.parser')
        if full := soup.find(class_="full"):
            message = list(full.stripped_strings)
            if not message[0].startswith("#!"):
                return
            language, code = message[0].removeprefix("#!").strip(), "\n".join(message[1:])
            if language not in self.languages:
                self.room.send(f"Unknown language: {language}")
                return
            threading.Thread(target = self.run, args = (event, language, code)).start()
        else:
            if match := re.match("(.+): ?(.+)", soup.get_text(strip = True)):
                language, code = match.groups()
                if language not in self.languages:
                    self.room.send(f"Unknown language: {language}")
                    return
                threading.Thread(target = self.run, args = (event, language, code)).start()
    def onPing(self, event):
        if event.content.endswith("help"):
            languages = "\n".join(self.languages)
            self.room.send(f"OLIMAR2 powered by Attempt This Online.\nPing Ginger for bot issues and pxeger for code-running issues.\nLanguages: {languages}")