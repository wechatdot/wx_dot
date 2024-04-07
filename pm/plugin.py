import time

from loguru import logger
from functools import wraps


from wxx import Msg, MsgType, WxClient

class PlugError(Exception):
    pass

class WxBot:
    __is_wx_plug = True
    def __init__(self):
        raise NotImplementedError

    def do(self, msg:Msg, wxclient: WxClient):
        raise NotImplementedError


class Condition:
    def __init__(self):
        self._legal = []
        self._illegal = []

    def _add_c(self, cs, c):
        if isinstance(c, list):
            cs.extend(c)
        else:
            cs.append(c)
    def add_cs(self, c):
        self._add_c(self._legal, c)

    def add_no_cs(self, c):
        self._add_c(self._illegal, c)

    @property
    def cs(self):
        return self._legal

    @property
    def no_cs(self):
        return self._illegal

    def check(self, c) -> bool:
        if "*" in self._legal:
            return True

        if "*" in self._illegal:
            return False

        if c in self._illegal:
            return False

        if len(self._legal) == 0:
            return True

        if c in self._legal:
            return True
        else:
            return False


class MsgCon:
    def __init__(self):
        self._type = Condition()
        self._from = Condition()
        self._room = Condition()
        self._kw   = Condition()
        self._no = False

    def no(self):
        self._no = not self._no
        return self

    def __add_con(self, con: Condition, value):
        if self._no:
            con.add_no_cs(value)
        else:
            con.add_cs(value)

    def from_id(self, value):
        self.__add_con(self._from, value)
        return self

    def room_id(self, value):
        self.__add_con(self._room, value)
        return self

    def istype(self, value):
        self.__add_con(self._type, value)
        return self

    def have_key(self, value):
        self.__add_con(self._kw, value)
        return self

    def __check_kw(self, msg: Msg) -> bool:
        if "*" in self._kw.cs:
            return True

        if self._kw.no_cs and msg.haveanykeywords(self._kw.no_cs):
            return False

        if self._kw.cs:
            if msg.haveanykeywords(self._kw.cs):
                return True
            else:
                return False
        else:
            return True

    def __check_cons(self, msg:Msg) -> bool:
        run_f = True
        run_f = run_f and self._from.check(msg.from_id)
        run_f = run_f and self._room.check(msg.room_id)
        run_f = run_f and self._type.check(msg.type)
        run_f = run_f and self.__check_kw(msg)
        return run_f

    # def __del__(self):
    #     print(f"MsgCon {id(self)} del!")

    def __call__(self, func):
        func.__is_wx_plug = True
        @wraps(func)
        def wrapper(*args, **kwargs):
            if (len(args) == 1) or isinstance(args[0], Msg):
                msg = args[0]
            else:
                msg = args[1]
            if self.__check_cons(msg):
                return func(*args, **kwargs)
            else:
                return

        return wrapper

