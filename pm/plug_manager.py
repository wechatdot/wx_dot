import importlib
import importlib.util
import os
import time
from functools import wraps
from pm import WxBot
import inspect
from loguru import logger
import threading
from concurrent.futures import ThreadPoolExecutor
import typing as _typing
from wxx import Msg
from wxx import WxClient

import schedule

wxsch = schedule.Scheduler()
wxsch_list = []


def _load_module_from_file(module_name, file_path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def _load_modules_from_dir(m_dir):
    ms = []
    for f in os.listdir(m_dir):
        if f.endswith('.py') and not f.startswith('__'):
            try:
                file_path = os.path.join(m_dir, f)
                module_name = f[:-3]  # Remove '.py' from filename
                module = _load_module_from_file(module_name, file_path)
                logger.debug(f"Module {module_name} has been loaded.")
                ms.append(module)
            except Exception as e:
                logger.error(f"Load plug in {f} fail, {e}")

    return ms


def singleton(cls):
    instances = {}
    @wraps(cls)
    def get_instance(*args, **kwargs):
        if cls not in instances:
            instances[cls] = cls(*args, **kwargs)
        return instances[cls]
    return get_instance


class WxPlugManager:
    def __init__(self,
                 plug_dir: str,
                 max_thread:int,
                 sleep_time:float,
                 msg_cb: _typing.Callable[..., _typing.List[Msg]],
                 wxclient: WxClient
        ):
        self.max_thread = max_thread
        self.sleep_time = sleep_time
        self.plug_dir = plug_dir
        self.msg_cb = msg_cb
        self.wxcient = wxclient

        self.__stop_event = threading.Event()
        self.__load_plug__()

    def __parse_mods(self, plugs):
        ms = []
        for p in plugs:
            for _attr in dir(p):
                if _attr.startswith("__"):
                    continue

                may_bot = getattr(p, _attr)

                if hasattr(may_bot, "_SchCon__sch_plug"):
                    continue

                if inspect.isfunction(may_bot) and hasattr(may_bot, "_MsgCon__is_wx_plug"):
                    ms.append(may_bot)

                if not inspect.isclass(may_bot):
                    continue

                if not issubclass(may_bot, WxBot):
                    continue

                if may_bot.__base__ == object:
                    continue

                try:
                    ms.append(may_bot().do)
                except Exception as e:
                    logger.error(f"init {may_bot} fail, {e}")

        return ms

    def __load_plug__(self):
        _ps = _load_modules_from_dir(self.plug_dir)
        self.__plugs = self.__parse_mods(_ps)

    def get_plugs(self):
        return self.__plugs

    def __handle_msg(self, msg):
        for p in self.__plugs:
            try:
                p(msg, self.wxcient)
            except Exception as e:
                logger.error(f"run func {p} fail!\n{e}\n")

    def __server(self):
        with ThreadPoolExecutor(max_workers=self.max_thread) as executor:
            while not self.__stop_event.is_set():
                for msg in self.msg_cb():
                    executor.submit(self.__handle_msg, msg)

                time.sleep(self.sleep_time)

    def set_wxclient(self, wxclient):
        self.wxcient = wxclient

    def set_msg_cb(self, msg_cb):
        self.msg_cb = msg_cb

    def start(self):
        self.__server_t = threading.Thread(target=self.__server)
        self.__server_t.start()

    def stop(self):
        self.__stop_event.set()
        self.__server_t.join()


class WxSchPlugManager:
    def __init__(self, plug_dir: str, wxclient: WxClient):
        self.plug_dir = plug_dir
        self.wxclient = wxclient
        self.__stop_event = threading.Event()
        self.__load_plug__()

    def __load_plug__(self):
        _load_modules_from_dir(self.plug_dir)

    def __server(self):
        while not self.__stop_event.is_set():
            wxsch.run_pending()
            time.sleep(1)
        logger.info(f"{self.__class__.__name__} exit!")

    def start(self):
        global wxsch_list
        for j,f in wxsch_list:
            if inspect.isclass(f):
                j.do(f().do, self.wxclient)
            elif inspect.isfunction(f):
                j.do(f, self.wxclient)
            else:
                pass

        self.__server_t = threading.Thread(target=self.__server)
        self.__server_t.start()

    def stop(self):
        self.__stop_event.set()
        self.__server_t.join()

