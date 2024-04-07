import queue
import time
import traceback

from . import client
from . import tcpserver

from queue import Queue
import threading
import socketserver
from loguru import logger

from wxx.msg import Msg, MsgType, MsgContainer
from wxx.contact import Contact, ChatRoom

from wxx.contact import get_friends, get_chatrooms

# for watchdog
from watchdog.observers import Observer
from wxx.filetool import WxImgFileEventHandler

import typing as _typing
import copy
import pickle

class WxError(Exception):
    pass


# noinspection SpellCheckingInspection
class WxClient:

    def __init__(self,
                 client_url:str = "http://127.0.0.1:19088",
                 server_ip:str = "127.0.0.1",
                 server_port:int = 19099,
                 max_msg_num:int = 1000,
                 wx_img_dat_dir:str = "./",
                 wx_img_dst:_typing.Optional[str] = None
                 ):

        # wxhelper server url
        self.client_url = client_url
        self.send_client = client.Client(self.client_url)

        if not self.__is_login():
            raise WxError("WeChat not login!\n")

        # server to get msg from wxhelper
        self.server_ip = server_ip
        self.server_port = server_port
        self.server_ip_port = (server_ip, server_port)

        self.max_msg_num = max_msg_num

        # watchdog watch dir
        self.wx_dat_dir = wx_img_dat_dir
        # copy decode image to img_dst
        self.img_dst = wx_img_dst

        # queue to save messages
        self.__msg_queue = Queue(maxsize=max_msg_num)

        self.__msgs_lock = threading.Lock()
        self.msgs: list[Msg] = []
        self.hist_msg: MsgContainer = MsgContainer()

        self._friends:_typing.Dict[str, Contact] = {}
        self._rooms:_typing.Dict[str, ChatRoom] = {}

        self.__stop_event = threading.Event()
        self.__init_server()
        self.__init_file_dog()
        self.__init_msg_parse()

    def __is_login(self) -> bool:
        login = {}
        try:
            login = self.send_client.check_login()
        except Exception as e:
            print(e)

        logger.debug(login)
        return login.get("code", 0) == 1

    def __init_server(self):
        self.__server = socketserver.ThreadingTCPServer(
            self.server_ip_port,
            lambda *args: tcpserver.WxTCPHandler(msg_queue=self.__msg_queue, *args)
        )
        self.__server_t = threading.Thread(target=self.__server.serve_forever, daemon=False)

    def __init_file_dog(self):
        observer = Observer()
        observer.schedule(WxImgFileEventHandler(self.img_dst), self.wx_dat_dir, recursive=True)
        self.__file_observer = observer

    def __init_msg_parse(self):
        self.__msg_parse_t = threading.Thread(target=self.__msg_parse)

    def __append_msg(self, msg:Msg):
        # new message for get_messages
        with self.__msgs_lock:
            self.msgs.append(msg)
        # all messages
        self.hist_msg.add_msg(msg)

        if msg.from_room:
            if msg.room_id not in self._rooms:
                self.__update_rooms()
            if msg.from_id not in self._rooms[msg.room_id].mems:
                self._rooms[msg.room_id].update_mems(self.send_client)

            if msg.room_id in self._rooms:
                self._rooms[msg.room_id].append_msg(msg)
            else:
                logger.error(f"{msg.room_id} not in {self._rooms.keys()}")
        else:
            if msg.from_id not in self._friends:
                self.__update_friends()

            if msg.from_id in self._friends:
                self._friends[msg.from_id].append_msg(msg)
            else:
                logger.error(f"{msg.from_id} not in {self._friends.keys()}")

    def __msg_parse(self):
        while not self.__stop_event.is_set():
            msg = None
            try:
                _m = self.__msg_queue.get(timeout=0.5)
                msg = Msg(_m)
                if msg.have_image():
                    self.send_client.download_attach(msg.msg_id)
            except queue.Empty:
                pass
            except Exception as e:
                logger.error(f"Get msg fail, {e}")
                break

            if msg != None:
                logger.debug(msg)
                try:
                    self.__append_msg(msg)
                except Exception as e:
                    traceback.print_exc()
                    print(e)

        logger.info(f"msg parse exit")

    def start(self):
        self.__server_t.start()
        self.__file_observer.start()
        self.__msg_parse_t.start()

        time.sleep(1)

        try:
            hook = self.send_client.hook_sync_msg(tcp_host=self.server_ip, tcp_port=f"{self.server_port}")
        except Exception as e:
            print(e)
            self.stop()

        hook = True
        if not hook:
            logger.error("hook fail, exit!\n")
            self.stop()
            raise WxError("hook msg error!\n")

        self._friends = get_friends(self.send_client)
        self._rooms = get_chatrooms(self.send_client)

    def stop(self):
        self.__stop_event.set()
        self.__server.server_close()
        self.__server.shutdown()
        self.__file_observer.stop()
        self.__msg_parse_t.join()

    def __update_friends(self, fs = None):
        _fs = fs if fs else get_friends(self.send_client)
        for k, f in _fs.items():
            if k not in self._friends:
                self._friends[k] = f

    def __update_rooms(self, rs = None):
        _rs = rs if rs else get_chatrooms(self.send_client, init_mems=False)
        for k, r in _rs.items():
            if k not in self._rooms:
                self._rooms[k] = r

        for _, r in self._rooms.items():
            r.update_mems(self.send_client)

    def get_contacts(self, update:bool = False) -> _typing.Dict[str, Contact]:
        if update:
            self.__update_friends()

        return self._friends

    def get_rooms(self, update:bool = False) -> _typing.Dict[str, ChatRoom]:
        if update:
            self.__update_friends()

        return self._rooms

    def get_new_msgs(self) -> list[Msg]:
        with self.__msgs_lock:
            ret = copy.deepcopy(self.msgs)
            self.msgs.clear()
        return ret

    def get_all_msgs(self) -> _typing.Dict[str, Msg]:
        return self.hist_msg.get_all_msgs()

    def send_re(self, msg: Msg, text: str, img: str = "", file: str = "") -> _typing.Any:
        if msg.from_room:
            reid = msg.room_id
        else:
            reid = msg.from_id

        self.send_client.send_msg(reid, text)
        if img:
            self.send_client.send_image(reid, img)
        if file:
            self.send_client.send_file(reid, file)


    def send_msg(self, wxid:str, text:str) -> _typing.Any:
        return self.send_client.send_msg(wxid, text)

    def send_room_msg(self, roomid:str, text:str) -> _typing.Any:
        return self.send_client.send_msg_to_room(roomid, text)

    def send_image(self, wxid:str, image:str) -> _typing.Any:
        return self.send_client.send_image(wxid, image)

    def send_at(self,
                wxid:_typing.Union[str, list[str]],
                roomid:str,
                msg:str,
                all:bool=False
        ) -> _typing.Any:
        return self.send_client.send_at(wxid, roomid, msg, all)

    def send_pat(self, wxid:str, receiver:str) -> _typing.Any:
        return self.send_client.send_pat(wxid, receiver)

    def send_file(self, wxid: str, filename:str) -> _typing.Any:
        return self.send_client.send_file(wxid, filename)

    def get_send_client(self):
        return copy.deepcopy(self.send_client)

    def clear_msg(self):
        self.hist_msg.clear()
        for _,f in self._friends.items():
            f.clear_msg()
        for _,r in self._rooms.items():
            r.clear_msg()

    def export(self, save_dir: str):
        to_save = {
            "friends": self._friends,
            "rooms": self._rooms,
            "msgs": self.hist_msg
        }

        with open(save_dir, 'wb') as f:
            pickle.dump(to_save, f)

    def load(self, load_dir: str):
        with open('data.pkl', 'rb') as f:
            loaded_data:dict = pickle.load(f)

        _fs = loaded_data.get("friends", None)
        if _fs:
            self.__update_friends(_fs)

        _rs = loaded_data.get("rooms", None)
        if _rs:
            self.__update_rooms(_rs)

        _ms = loaded_data.get("msgs", None)
        if _ms:
            self.hist_msg = _ms
