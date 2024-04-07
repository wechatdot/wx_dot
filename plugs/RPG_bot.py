import re
import typing

import openai
from wxx import Msg, MsgType
from wxx import WxClient
from pm import WxBot
from pm import MsgCon
from loguru import logger

import typing as _typing
import copy
import threading
import os

from web_tool import download_image, download_file

rpg_prompt = """
扮演给定角色，模仿他们的语言、语调和独特特点。您的回答应仅包含角色所知道的知识。请记住以下几点：
1.  重要：回复消息要十分简洁, 除了创作文学作品之外每次回复字数不能超过30字。
2.  模仿他们的举止和口头禅。
3.  反映角色的态度和独特癖好。
4.  考虑他们的文化和教育背景。
您的目标是通过对话和动作创造一个真实而引人入胜的角色刻画。一旦我指定了角色，请以该角色的详细介绍作为回答。
"""

def get_env(_env:str):
    return os.environ.get(_env)


class RPG:
    def __init__(self, wxid: str, role: str):
        self.wxid = wxid
        self.ai_msgs = [
            {"role": "system", "content": rpg_prompt},
            {"role": "user", "content": f"开始扮演{role}"},
            {"role": "assistant", "content": f"好的，接下来我将以{role}的身份与你对话"},
            {"role": "user", "content": "简单介绍一下你自己"},
        ]

        self._init_msgs = self.ai_msgs
        self._lock = threading.Lock()

        self.client = openai.OpenAI(
            # api_key=get_env("OPENAI_API_KEY"),
            api_key="sk-1ei0pIAhLsACJE8XF6Dc8146F79841F7A9Ab9f59C3C0E9B2",
            base_url="http://192.168.2.2:3000/v1/"
        )

    def __ai_chat(self, msg: Msg):

        total_len = 0
        for m in self.ai_msgs:
            total_len += len(m.get("content", ""))

        if total_len > 1000 or len(self.ai_msgs) > 10:
            self.ai_msgs = self._init_msgs

        try_time = 3
        res = ""
        temp_msg = copy.deepcopy( self.ai_msgs)
        if msg:
            temp_msg.append({"role": "user", "content": "".join(msg.content.split("\u2005")[1])})
        print(temp_msg)
        for i in range(try_time):
            try:
                print(self.ai_msgs)
                completion = self.client.chat.completions.create(
                    model="gpt-3.5-turbo-16k",
                    messages=temp_msg,
                    timeout = 7
                )
                res = completion.choices[0].message.content
            except Exception as e:
                logger.error(e)

            if res:
                break
        return res

    def chat(self, msg: Msg = None) -> str:
        res = ""
        with self._lock:
            res = self.__ai_chat(msg)
            logger.info(res)

        if res:
            if msg is not None:
                self.ai_msgs.append({"role": "user", "content": "".join(msg.content.split("\u2005")[1])})
            self.ai_msgs.append({"role": "assistant", "content": res})

        return res

class RPGBot(WxBot):
    def __init__(self):
        self.name = "rpg"
        self.admin_id = get_env("ADMIN_WXID")
        self.rpgs: _typing.Dict[str, RPG] = {}
        logger.info("RPGBot initialized")

    def do_manager(self, msg: Msg, wxc: WxClient) -> bool:
        logger.info("RPGBot do_manager")

        if msg.havekeyword("/rpgend"):
            logger.info("RPGBot rpgend")
            if msg.room_id in self.rpgs:
                self.rpgs.pop(msg.room_id)

            return True

        if msg.havekeyword("/rpg"):
            _r = msg.content.split("/rpg")[-1]

            if not _r:
                return True

            self.rpgs[msg.room_id] = RPG(msg.room_id, _r)
            res_str = self.rpgs[msg.room_id].chat()
            if res_str:
                logger.info(res_str)
                wxc.send_re(msg=msg, text=res_str)

            return True

        if self.__id_started(msg.room_id):
            return False
        else:
            return True

    def __id_started(self, wxid):
        if self.rpgs.get(wxid, None) is None:
            return False
        else:
            return True

    @MsgCon().istype(MsgType.AT)
    def do(self, msg: Msg, wxclient: WxClient = None):

        logger.info(f"RPGBot received {msg}")

        if self.do_manager(msg, wxclient):
            return

        if msg.room_id in self.rpgs:
            res = self.rpgs[msg.room_id].chat(msg)
            if res:
                logger.info(res)
                img = ""
                mp3 = ""
                if res.find("![Image]") != -1:
                    try:
                        img_url = res.split("![Image]")[0]
                        img = download_image(img_url,"D:\\temp\\", from_id="")
                    except Exception as e:
                        logger.error(e)

                _mp3 = re.findall(r'https?://[^\s]+\.(?:mp3)', res)
                if len(_mp3) > 0:
                    mp3 = download_file(_mp3[0], "D:\\temp\\")

                wxclient.send_re(msg=msg, text=res, img=img, file=mp3)


