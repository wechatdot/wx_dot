from pm import MsgCon
from wxx import WxClient
from wxx import Msg
from wxx import MsgType
from pm import WxBot
from loguru import logger

@MsgCon()
def debug_bot(msg, wxc):
    logger.debug(f"Get: {msg}")