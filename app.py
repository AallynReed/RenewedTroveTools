import json
import socket
import sys

import psutil

from main import App

app = App()

if __name__ == "__main__":
    arguments = sys.argv[1:]
    processes = [
        p.info["pid"]
        for p in psutil.process_iter(attrs=["pid", "name", "exe"])
        if p.info["name"] == "RenewedTroveTools.exe"
    ]
    conns = psutil.net_connections()
    connections = []
    if processes:
        for conn in conns:
            if conn.laddr.port in range(13010, 13020):
                if conn.pid in processes:
                    connections.append(conn)
                    if arguments:
                        server = socket.create_connection((conn.laddr.ip, conn.laddr.port))
                        server.sendall(json.dumps(arguments).encode())
                    break
    if not connections:
        app.run()

