# wx_dot

wechat bot

base on https://github.com/ttttupup/wxhelper

## 使用方式

- 启动微信

- 下载wxhelper dll文件 https://github.com/ttttupup/wxhelper/releases/tag/3.9.8.25-v2

- 使用wxhelper中的dll和注入工具注入dll
    可以参考：
    https://github.com/ttttupup/wxhelper/discussions/65
    https://github.com/ttttupup/wxhelper/tree/main/tool/injector

- 修改bot.py 中的配置
```python
class DotBot:

    def __init__(self, plug: str):
        print("init client")
        wxclient = WxClient(
            # 修改为你的wxid
            wx_img_dat_dir="C:\\document\\WeChat Files\\your_wxid\\wxhelper\\image",
            # 修改微信图片接收之后存储的位置
            wx_img_dst="D:\\path\\to\\image\save\\"
        )

        self.pm = WxPlugManager(plug, 100, 1, wxclient.get_new_msgs, wxclient)
        self.s_pm = WxSchPlugManager(plug, wxclient)
        self.wxclient = wxclient

... ...
```

- 启动机器人
```powershell
python bot.py

```


## 自定义插件编写

请参考 plugs 文件下下面的文件

- 编写接收到消息时触发的机器人
```python
from pm import MsgCon
from wxx import WxClient
from loguru import logger

#注册一个函数，当收到的消息中没有字符串 “hello”时触发
@MsgCon().no().have_key("hello")
def no_hello_bot(msg, wxc: WxClient):
    logger.info(f"plus name is no_hello_bot")
    logger.debug(f"no_hello_bot: {msg}")

```

- 编写一个定时触发的机器人
```python
from pm import SchCon, wxsch
from loguru import logger


# 注册一个函数，每分钟执行一次
@SchCon(wxsch.every(1).minute)
def hello(wxclient):
    logger.info(f"bot every minute")
    logger.debug(f"hello {wxclient}")

```


## 版权声明 & 特别提示

[wx_dot](https://github.com/diandianti/wx_dot) 是供学习交流的开源项目，代码及其制品仅供参考，不保证质量，不构成任何商业承诺或担保，不得用于商业或非法用途，使用者自行承担后果。
