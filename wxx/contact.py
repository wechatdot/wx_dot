
import typing as _typing
from wxx.msg import Msg, MsgType, MsgContainer
from wxx.client import Client
from loguru import logger

import re

room_mem_split_char = "^G"

class RevokeMsg(Msg):
    def __init__(self, nick, msg):
        self.nick = nick
        self.msg = msg

    def __repr__(self):
        _s = super().__repr__()
        _s += f"from: {self.nick}"

class Contact:
    def __init__(self, wxid:str, nick:str):
        self.nick = nick
        self.wxid = wxid
        self.re_msgs: MsgContainer = MsgContainer()
        self.msgs: MsgContainer = MsgContainer()

        self.__revoke_msgid = re.compile(r"<newmsgid>(\d+)</newmsgid>")
        self.__revoke_nick = re.compile(r'<replacemsg><!\[CDATA\[(.+)\]\]></replacemsg>')

    def clear_msg(self):
        self.msgs.clear()
        self.re_msgs.clear()

    def append_msg(self, msg:Msg) -> _typing.Optional[RevokeMsg]:
        self.msgs.add_msg(msg)
        if msg.type == MsgType.REVOKE:
            _content = msg.content
            _wxid = _content.split(':\n')[0]
            _msgId = self.__revoke_msgid.search(_content)
            _nick = self.__revoke_nick.search(_content)

            if _msgId and _nick:
                who = _nick.group(1)
                logger.debug(f"{who} 撤回消息，已记录")
                remsg: Msg = self.msgs.get_msg(_msgId.group(1))
                self.re_msgs.add_msg(RevokeMsg(who, remsg))
                return remsg

        return None

    def __str__(self):
        return f"nick:{self.nick} wxid:{self.wxid}"

    def __repr__(self):
        return str(self)

class RoomMem(Contact):
    def __init__(self, wxid:str, nick:str, roomid:str):
        self.roomid = roomid
        super().__init__(wxid, nick)

    def __str__(self):
        return f"Room:{self.roomid} nick:{self.nick} wxid:{self.wxid}"

class ChatRoom:
    def __init__(self, roomid:str, name:str):
        self.roomid = roomid
        self.name = name
        self.mems:_typing.Dict[str, RoomMem] = {}
        self.msgs:MsgContainer = MsgContainer()
        self.remsgs:MsgContainer = MsgContainer()

    def __str__(self):
        _ms = ""
        for _, m in self.mems.items():
            _ms += f"\t{m}\n"
        return (f"roomid:{self.roomid}  name:{self.name}\n" + _ms)

    def __repr__(self):
        return str(self)

    def clear_msg(self):
        self.msgs.clear()
        for _, m in self.mems.items():
            m.clear_msg()

    def append_msg(self, msg:Msg):
        self.msgs.add_msg(msg)

        if msg.from_id not in self.mems:
            logger.error(f"{msg.from_id} not in {self.mems.keys()}")
            return

        remsg = self.mems[msg.from_id].append_msg(msg)
        if remsg is not None:
            self.remsgs.add_msg(remsg)

    def update_mems(self, client:Client):

        try:
            res = client.get_member_from_chatroom(self.roomid)
        except Exception as e:
            logger.error(e)
            return

        if res.get("code", -1) == -1:
            logger.error(f"Get chat room {self.roomid} users fail!")
            return

        data = res.get("data")
        logger.debug(f"wxids is {data.get('members')}")
        wxids = data.get('members', "").split(room_mem_split_char)

        logger.debug(f"{wxids}")

        for i in wxids:
            if not i:
                continue

            if i in self.mems:
                continue

            try:
                res = client.get_contact_profile(i)
            except Exception as e:
                logger.error(e)
                continue

            if res.get("code", 0) > 0:
                nick = res.get("data", {}).get("nickname", "")
                self.mems[i] = RoomMem(i, nick, self.roomid)


def isroomid(wxid: str) -> bool:
    return len(wxid) >= 9 and wxid[-9:] == "@chatroom"


def get_friends(client:Client):
    friends: _typing.Dict[str, Contact] = {}
    try:
        res = client.get_contact_list()
    except Exception as e:
        logger.error(e)
        return friends

    if res.get("msg", "") != "success":
        logger.error("Get rooms fail!")
        return friends

    for i in res.get("data"):
        logger.debug(i)
        wxid:str = i.get("wxid", "")
        if not isroomid(wxid):
            friends[wxid] = Contact(wxid, i.get("nickname", ""))
    return friends

def get_chatrooms(client: Client, init_mems:bool = True):
    rooms: _typing.Dict[str, ChatRoom] = {}
    try:
        res = client.get_contact_list()
    except Exception as e:
        logger.error(e)
        return rooms

    if res.get("msg", "") != "success":
        logger.error("Get rooms fail!")
        return rooms

    for i in res.get("data"):
        logger.debug(i)
        wxid:str = i.get("wxid", "")
        if isroomid(wxid):
            rooms[wxid] = ChatRoom(wxid, i.get("nickname"))
            if init_mems:
                rooms[wxid].update_mems(client)

    return rooms
