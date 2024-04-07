from pm import SchCon, wxsch
from pm import WxBot
from loguru import logger


# @SchCon(wxsch.every(2).seconds)
# class EveryBot(WxBot):
#     def __init__(self):
#         self.name = "every bot"
#
#     def do(self, wxclient):
#         logger.info(f"bot name {self.name}")
#         logger.debug(f"get arg {wxclient}")

@SchCon(wxsch.every(1).minute)
def hello(wxclient):
    logger.info(f"bot every minute")
    logger.debug(f"hello {wxclient}")


