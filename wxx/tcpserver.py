import json
import threading
import socketserver
import queue

from loguru import logger


class WxTCPHandler(socketserver.BaseRequestHandler):
    def __init__(self,
                 request,
                 client_address,
                 server,
                 msg_queue: queue.Queue):
        logger.debug("new connect!")
        self.msg_queue: queue.Queue = msg_queue
        super().__init__(request, client_address, server)

    def __del__(self):
        logger.debug("del handl")

    def handle(self):
        conn = self.request
        while True:
            logger.debug("still run")
            try:
                ptr_data = b""
                while True:
                    data = conn.recv(1024)
                    ptr_data += data
                    if len(data) == 0 or data[-1] == 0xA:
                        break

                logger.debug(ptr_data)
                msg = json.loads(ptr_data)
                self.msg_callback(msg)

            except OSError as e:
                break
            except json.JSONDecodeError as e:
                logger.error(f"json decode error {e}")
                pass
            conn.sendall("200 OK".encode())
            conn.close()

    def msg_callback(self, msg):
        logger.debug(f"get msg and put in Queue {msg}")
        self.msg_queue.put(msg)


def start_socket_server(
        msg_queue: queue.Queue,
        ip: str = "127.0.0.1",
        port: int = 19099,
        request_handler=WxTCPHandler,
        main_thread: bool = True
    ) -> int or None:
    ip_port = (ip, port)
    try:
        s = socketserver.ThreadingTCPServer(ip_port, lambda *args: request_handler(msg_queue=msg_queue, *args))
        if main_thread:
            s.serve_forever()
        else:
            socket_server = threading.Thread(target=s.serve_forever, daemon=False)
            socket_server.start()
            return socket_server.ident
    except KeyboardInterrupt as e:
        logger.info(f"Get {e}")
    except Exception as e:
        logger.error(e)
    return



