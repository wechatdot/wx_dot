import sys
import time
from loguru import logger

from wxx import WxClient
from pm import WxSchPlugManager, WxPlugManager

class DotBot:

    def __init__(self, plug: str):
        print("init client")
        wxclient = WxClient(
            wx_img_dat_dir="C:\\document\\WeChat Files\\your_wxid\\wxhelper\\image",
            wx_img_dst="D:\\path\\to\\image\save\\"
        )

        self.pm = WxPlugManager(plug, 100, 1, wxclient.get_new_msgs, wxclient)
        self.s_pm = WxSchPlugManager(plug, wxclient)
        self.wxclient = wxclient

    def run(self):
        self.wxclient.start()
        self.pm.start()
        self.s_pm.start()
        try:
            while True:
                time.sleep(2)
        except KeyboardInterrupt as e:
            print(f"get {e}, exit")

        self.s_pm.stop()
        self.pm.stop()
        self.wxclient.stop()

def main():
    logger.remove()
    logger.add(sys.stdout, level="INFO")
    bot = DotBot("./plugs")
    bot.run()

if __name__ == "__main__":
    main()

