#!/usr/bin/env python3
import logging
from datetime import datetime
import socket
import sys
import threading
import time

from flaskUtils import app, board_lock, initialize_presets, run_schedules
from LEDUtils import PPB
from werkzeug.serving import ThreadedWSGIServer, make_server


class IPv6OnlyWSGIServer(ThreadedWSGIServer):
    def server_bind(self):
        self.socket.setsockopt(socket.IPPROTO_IPV6, socket.IPV6_V6ONLY, 1)
        return super().server_bind()


def serve(server):
    server.serve_forever()


def start_servers():
    servers = [make_server('0.0.0.0', 5000, app, threaded=True)]
    try:
        servers.append(IPv6OnlyWSGIServer('::', 5000, app))
    except (OSError, SystemExit) as error:
        logging.warning("IPv6 listener unavailable: %s", error)
    for server in servers:
        threading.Thread(target=serve, args=(server,), daemon=True).start()
    return servers


def update_board():
    PPB.displayString[:] = ['', '']
    for entry in PPB.content:
        kind, line = entry.split(' ')
        if kind in ('time', 'date', 'text', 'weather'):
            getattr(PPB, kind)(int(line))
    for line in range(PPB.lineCount):
        if PPB.animationSpeed[line] != 0:
            PPB.updateTextAnimation(line)
    PPB.updateDisplayString()
    PPB.updateBoardColors()


if __name__ == '__main__':
    with board_lock:
        initialize_presets()
    start_servers()
    last_minute = datetime.now().replace(second=0, microsecond=0)
    while True:
        with board_lock:
            now = datetime.now()
            minute = now.replace(second=0, microsecond=0)
            if minute != last_minute:
                last_minute = minute
                run_schedules(now)
            if getattr(PPB, 'restart_at', None) and time.monotonic() >= PPB.restart_at:
                sys.exit(1)
            update_board()
        time.sleep(0.01)
