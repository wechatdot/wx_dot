from PIL import Image
import io
import shutil
import os

from watchdog.events import FileSystemEventHandler

def parseInt(s):
    res = None
    try:
        res = int(s)
    except Exception:
        pass
    return res


def dat_to_png(file_path:str) -> str:
    try:
        with open(file_path, 'rb') as f:
            img_data = f.read()
            image = Image.open(io.BytesIO(img_data))
            ext_len = -len(file_path.split(".")[-1])
            new_name = file_path[:ext_len] + "png"
            image.save(new_name)
            return new_name
    except IOError:
        return ""


def copyTo(src, dst):
    print(f"{src} -> {dst}")
    try:
        print(os.path.isfile(src))
        shutil.copy2(src, dst)
    except Exception as e:
        print(e)


class WxImgFileEventHandler(FileSystemEventHandler):

    def __init__(self, imgdst:str):
        self.imgdst = imgdst
        super().__init__()

    def on_moved(self, event):
        if not event.is_directory:
            dst = event.dest_path
            if dst.split(".")[-1] == "dat" and dst[-6] != "_":
                try:
                    print("Copy file")
                    shutil.copy2(dst, self.imgdst)
                except Exception as e:
                    print(e)
