"""
send message and get userinfo

more about api https://github.com/ttttupup/wxhelper/blob/main/doc/3.9.5.81.md
"""

import requests
import json

from typing import Any
from typing import Union
import threading
from functools import wraps
from loguru import logger

default_headers = {
    'Content-Type': 'application/json'
}

def method_synchronized(method):
    @wraps(method)
    def synchronized_method(self, *args, **kwargs):
        if not hasattr(self, "_lock"):
            raise AttributeError("This instance does not have a lock.")
        with self._lock:
            return method(self, *args, **kwargs)
    return synchronized_method


class Client:

    def __init__(self, url):
        self.url = url
        self._lock = threading.Lock()

    def __post(self, url: str, payload, headers=None) -> Any:
        if headers is None:
            headers = default_headers
        res = requests.request("POST", url, headers=headers, data=payload)
        # logger.debug(res.json())
        return res.json()

    @method_synchronized
    def check_login(self) -> Any:
        """
         return example
            {
                "code": 1,
                "msg": "success",
                "data":null
            }
        """

        url = f"{self.url}/api/checkLogin"
        return self.__post(url, {}, headers={})

    @method_synchronized
    def user_info(self) -> Any:
        """
        return example
        {
            "code": 1,
            "data": {
                "account": "xxx",
                "city": "Zhengzhou",
                "country": "CN",
                "currentDataPath": "C:\\WeChat Files\\wxid_xxx\\",
                "dataSavePath": "C:\\wechatDir\\WeChat Files\\",
                "dbKey": "965715e30e474da09250cb5aa047e3940ffa1c8f767c4263b132bb512933db49",
                "headImage": "https://wx.qlogo.cn/mmhead/ver_1/MiblV0loY0GILewQ4u2121",
                "mobile": "13949175447",
                "name": "xxx",
                "province": "Henan",
                "signature": "xxx",
                "wxid": "wxid_22222"
            },
            "msg": "success"
        }
        """
        url = f"{self.url}/api/userInfo"
        return self.__post(url, {}, headers={})

    @method_synchronized
    def hook_sync_msg(self,
                      tcp_host: str = "127.0.0.1",
                      tcp_port: str = "19099",
                      timeout: int = 3000,
                      http_server: str = "http://localhost:8080") -> bool:
        """
        :param tcp_host:
        :param tcp_port:
        :param timeout:
        :param http_server:
        :return:
        {"code":0,"msg":"success","data":null}
        """

        url = f"{self.url}/api/hookSyncMsg"
        payload = json.dumps({
            "port": tcp_port,
            "ip": tcp_host,
            "url": http_server,
            "timeout": str(timeout),
            "enableHttp": "0"
        })

        logger.debug(payload)

        res = self.__post(url, payload)

        logger.debug(res)
        if res is None:
            return False
        else:
            return res.get("code") != "0"

    @method_synchronized
    def get_member_from_chatroom(self, wxid: str) -> Any:
        """
        :param wxid:
        :return:
        {
            "code": 1,
            "data": {
                "admin": "wxid_2222",
                "adminNickname": "123",
                "chatRoomId": "22224@chatroom",
                "memberNickname": "^G123^G^G",
                "members": "wxid_2222^Gwxid_333"
            },
            "msg": "success"
        }
        """
        url = f"{self.url}/api/getMemberFromChatRoom"
        payload = json.dumps({
            "chatRoomId": f"{wxid}"
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_msg(self, wxid: str, msg: str) -> Any:
        """
        :param wxid:
        :param msg:
        :return:
        example {"code":345686720,"msg":"success","data":null}
        """
        url = f"{self.url}/api/sendTextMsg"

        payload = json.dumps({
            "wxid": wxid,
            "msg": msg
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_msg_to_room(self, wxid: str, msg: str) -> Any:
        """
        like send_msg but for chatroom
        :param wxid:
        :param msg:
        :return:
        """
        url = f"{self.url}/api/sendTextMsg"
        if len(wxid) >= 9 and wxid[-9:] == "@chatroom":
            payload = json.dumps({
                "wxid": wxid,
                "msg": msg
            })
        else:
            payload = json.dumps({
                "wxid": f"{wxid}@chatroom",
                "msg": msg
            })
        return self.__post(url, payload)

    @method_synchronized
    def get_contact_list(self) -> Any:
        """
        :return:
        {
            "code": 1,
            "data": [
                {
                   "customAccount": "",
                    "encryptName": "v3_020b3826fd03010000000000e04128fddf4d90000000501ea9a3dba12f95f6b60a0536a1adb6b40fc4086288f46c0b89e6c4eb8062bb1661b4b6fbab708dc4f89d543d7ade135b2be74c14b9cfe3accef377b9@stranger",
                    "nickname": "文件传输助手",
                    "pinyin": "WJCSZS",
                    "pinyinAll": "wenjianchuanshuzhushou",
                    "reserved1": 1,
                    "reserved2": 1,
                    "type": 3,
                    "verifyFlag": 0,
                    "wxid": "filehelper"
                }
            ].
            "msg": "success"
        }
        """
        url = f"{self.url}/api/getContactList"
        return self.__post(url, {}, headers={})

    @method_synchronized
    def download_attach(self, msg_id) -> Any:
        """
        :param msg_id:
        :return:
        {
            "code": 1,
            "data": {},
            "msg": "success"
        }
        """
        url = f"{self.url}/api/downloadAttach"
        payload = json.dumps({
            "msgId": msg_id
        })
        return self.__post(url, payload)

    @method_synchronized
    def decode_image(self, dat: str, dst: str) -> Any:
        """
        :param dat:
        :param dst:
        :return:
        {
            "code": 1,
            "data": {},
            "msg": "success"
        }
        """

        url = f"{self.url}/api/decodeImage"
        payload = json.dumps({
            "filePath": dat,
            "storeDir": dst
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_image(self, wxid: str, img: str) -> Any:
        """
        :param wxid:
        :param img:
        :return:
        {
            "code": 1,
            "data": {},
            "msg": "success"
        }
        """
        url = f"{self.url}/api/sendImagesMsg"
        payload = json.dumps({
            "wxid": wxid,
            "imagePath": img
        })
        return self.__post(url, payload)

    @method_synchronized
    def get_contact_profile(self, wxid: str) -> Any:
        """
        :param wxid:
        :return:
        {
            "code": 1,
            "data": {
                "account": "account",
                "headImage": "https://wx.qlogo.cn/mmhead/ver_1/0",
                "nickname": "test",
                "v3": "wxid_123",
                "wxid": "wxid_123"
            },
            "msg": "success"
        }
        """
        url = f"{self.url}/api/getContactProfile"
        payload = json.dumps({
            "wxid": wxid
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_at(self,
                wxid: Union[str, list[str]],
                room_id: str,
                msg: str,
                at_all: bool = False
                ) -> Any:
        """
        :param wxid:
        :param room_id:
        :param msg:
        :param at_all:
        :return:
        {
            "code": 67316444768,
            "data": null,
            "msg": "success"
        }
        """

        at_ids = ""
        if at_all:
            at_ids = "notify@all"
        elif isinstance(wxid, list):
            for i in wxid:
                at_ids += f"{i},"
            at_ids.strip(",")
        else:
            at_ids = wxid

        url = f"{self.url}/api/sendAtText"
        payload = json.dumps({
            "wxids": at_ids,
            "chatRoomId": room_id,
            "msg": msg
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_pat(self, wxid: str, receiver: str) -> Any:
        """
        :param wxid:
        :param receiver:
        :return:
        {
            "code": 1,
            "data": {},
            "msg": "success"
        }
        """
        url = f"{self.url}/api/sendPatMsg"

        payload = json.dumps({
            "wxid": wxid,
            "receiver": receiver,
        })
        return self.__post(url, payload)

    @method_synchronized
    def send_file(self, wxid: str, file_path: str):
        url = f"{self.url}/api/sendFileMsg"
        payload = json.dumps({
            "wxid": wxid,
            "filePath": file_path
        })
        return self.__post(url, payload)


if __name__ == "__main__":
    client = Client("http://127.0.0.1:19088")
    log_in = client.check_login()
    if log_in:
        print(client.user_info())
    else:
        print("log in fail!")
