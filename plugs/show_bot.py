from pm import MsgCon
from wxx import WxClient
from wxx import Msg
from wxx import MsgType
from pm import WxBot
from loguru import logger


class Bot(WxBot):
    def __init__(self):
        self.name = "bot1"

    @MsgCon().istype(MsgType.TEXT).have_key("hello")
    def do(self, msg: Msg, wxclient: WxClient = None):
        logger.info(f"plus name is {self.name}")
        logger.debug(f"get msg with 'hello' --- {msg}")

        if msg.from_room:
            res_name = wxclient.get_rooms()[msg.room_id].mems[msg.from_id].nick
            wxclient.send_pat(msg.from_id, msg.room_id)
            wxclient.send_msg(msg.room_id, f"hello {res_name}")
        else:
            res_name = wxclient.get_contacts()[msg.from_id].nick
            wxclient.send_msg(msg.from_id, f"hello {res_name}")

@MsgCon().istype(MsgType.AT).have_key("消息数目")
def msg_count(msg: Msg, wxclient: WxClient = None):
    logger.info(f"plus name is msg_count")

    if msg.from_room:
        room_mem = wxclient.get_rooms()[msg.room_id].mems[msg.from_id]
        nick = room_mem.nick
        count = room_mem.msgs.msg_count()

        wxclient.send_msg(msg.room_id, f"{nick} 消息数 {count}")


@MsgCon().istype(MsgType.AT).have_key("消息统计")
def msg_total(msg: Msg, wxclient: WxClient = None):
    logger.info(f"plus name is msg_total")

    if msg.from_room:
        room_mems = wxclient.get_rooms()[msg.room_id].mems
        sort_res = []
        for _, m in room_mems.items():
            sort_res.append(
                (m.nick, m.msgs.msg_count())
            )
        sort_res.sort(key=lambda x: x[1], reverse=True)
        logger.info(sort_res)

        icons = ["🥇", "🥈", "🥉"]

        res = "消息统计:\n"
        for idx, (n, c) in enumerate(sort_res):
            if c == 0:
                break

            if idx < 3:
                res += f"{icons[idx]} {n} {c}\n"
            else:
                res += f"{n} {c}\n"

        wxclient.send_msg(msg.room_id, res)

@MsgCon().istype(MsgType.PATME)
def do_not_patme(msg: Msg, wxclient: WxClient = None):
    logger.info(f"plug name {do_not_patme}")
    if msg.from_room:
        res_name = wxclient.get_rooms()[msg.room_id].mems[msg.from_id].nick
        wxclient.send_pat(msg.from_id, msg.room_id)
        wxclient.send_msg(msg.room_id, f"不要拍我 {res_name}")
    else:
        res_name = wxclient.get_contacts()[msg.from_id].nick
        wxclient.send_msg(msg.from_id, f"不要拍我 {res_name}")

