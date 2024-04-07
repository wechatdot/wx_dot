import copy
from enum import IntEnum
from loguru import logger

from collections import OrderedDict as MsgDict
import typing as _typing
import re
from threading import Lock

class MsgType(IntEnum):
    TEXT = 1
    IMAGE = 3
    VIDEO = 43
    STICKER = 47
    REFERENCE = 49
    MONEY = 10000
    REVOKE = 10002
    PAT = 66666
    PATME = 66667
    AT = 99999
    OTHERS = -1

    def __str__(self):
        if self == MsgType.TEXT:
            return "文本信息"
        elif self == MsgType.IMAGE:
            return "图片"
        elif self == MsgType.VIDEO:
            return "视频"
        elif self == MsgType.STICKER:
            return "微信表情"
        elif self == MsgType.REFERENCE:
            return "引用消息"
        elif self == MsgType.REVOKE:
            return "撤回消息"
        elif self == MsgType.PAT:
            return "拍一拍"
        elif self == MsgType.PATME:
            return "拍了拍我"
        elif self == MsgType.AT:
            return "@消息"
        elif self == MsgType.MONEY:
            return "红包"
        else:
            return "未知类型"

    def __eq__(self, other):
        if isinstance(other, int):
            return self.value == other
        elif isinstance(other, str):
            return str(self.value) == other
        elif isinstance(other, MsgType):
            return self.value == other.value
        else:
            return False

    @classmethod
    def parse(cls, msg):

        content = msg.get("content", "")
        if content.find('<sysmsg type="pat">') != -1:
            return MsgType.PAT

        _t = int(msg.get("type", "-2"))
        if _t == 1 and msg.get("displayFullContent").find("在群聊中@了你") != -1:
            return MsgType.AT
        if _t in MsgType.__members__.values():
            return MsgType(_t)
        else:
            return MsgType.OTHERS


def id_is_room(user:str)->bool:
    return len(user) >= 9 and user[-9:] == "@chatroom"


class Msg:
    def __init__(self, raw : dict):
        self.raw = raw
        self.__parse()

    def __parse(self):
        if not isinstance(self.raw, dict):
            return
        self.type = MsgType.parse(self.raw)
        self.msg_id = str( self.raw.get('msgId', ""))
        self.from_id = self.raw.get("fromUser", "")
        self.content = self.raw.get("content", "")
        self.to_id = ""
        self.room_id = self.from_id
        self.from_room: bool = False

        if id_is_room(self.from_id):
            self.from_room = True
            self.from_id = self.content.split(':\n')[0]

        if self.type == MsgType.PAT:
            match = re.search(r"<fromusername>(.*?)</fromusername>", self.content)
            if match:
                self.from_id = match.group(1)
            if self.content.find("拍了拍我") != -1:
                self.type = MsgType.PATME

    def __del__(self):
        pass
        # logger.debug("Msg del")

    def __repr__(self):
        return (f"Msg:"
                f"  id: {id(self)}"
                f"  content: {self.content}"
                f"  type:{self.type}"
                f"  msg_id:{self.msg_id}"
                f"  from:{self.from_id}"
                f"  room:{self.room_id}"
                f"  raw: {self.raw}")

    def __str__(self):
        return self.__repr__()

    def have_image(self) -> bool:
        return self.type == MsgType.IMAGE

    def have_media(self) -> bool:
        return self.type == MsgType.IMAGE or self.type == MsgType.VIDEO

    # def __fromchatroom(self):
    #     return idIsRoom(self.from_id)

    def havekeyword(self, key: str) -> bool:
        res = self.content.find(key) != -1
        return res

    def haveanykeywords(self, keys:list[str]) -> bool:
        for key in keys:
            if self.havekeyword(key):
                return True

        return False


class MsgContainer:
    def __init__(self):
        self.__lock = Lock()
        self._msg_dict = MsgDict()

    def add_msg(self, msgs: _typing.Union[_typing.Iterable, Msg]):
        if isinstance(msgs, Msg):
            with self.__lock:
                self._msg_dict[msgs.msg_id] = msgs
        else:
            with self.__lock:
                for m in msgs:
                    self._msg_dict[m.msg_id] = m

    def get_msg(self, msg_id: str) -> _typing.Optional[Msg]:
        return self._msg_dict.get(msg_id, None)

    def msg_count(self):
        return len(self._msg_dict)

    def get_all_msgs(self) -> _typing.Optional[MsgDict]:
        with self.__lock:
            ret = copy.deepcopy(self._msg_dict)
        return ret

    def clear(self):
        self._msg_dict.clear()

