
from pm import MsgCon
from wxx import WxClient
from wxx import Msg
from wxx import MsgType
from pm import WxBot
from loguru import logger

@MsgCon().no().have_key("hello")
def no_hello_bot(msg, wxc: WxClient):
    logger.info(f"plus name is no_hello_bot")
    logger.debug(f"no_hello_bot: {msg}")

