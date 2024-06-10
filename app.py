import json
import socket
import sys

import psutil

from main import App

import ctypes
import platform


# Function to set DPI awareness
def set_dpi_unaware():
    if platform.system() == "Windows":
        # Constants for the DPI awareness context
        DPI_AWARENESS_CONTEXT_UNAWARE = -1

        # Load user32.dll
        user32 = ctypes.windll.user32

        # Function prototype
        set_process_dpi_awareness_context = user32.SetProcessDpiAwarenessContext
        set_process_dpi_awareness_context.argtypes = [ctypes.c_void_p]
        set_process_dpi_awareness_context.restype = ctypes.c_bool

        # Set the DPI awareness context to DPI_AWARENESS_CONTEXT_UNAWARE
        result = set_process_dpi_awareness_context(
            ctypes.c_void_p(DPI_AWARENESS_CONTEXT_UNAWARE)
        )

        if not result:
            print("Failed to set DPI awareness context to UNAWARE")
        else:
            print("Successfully set DPI awareness context to UNAWARE")


# set_dpi_unaware()

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
                        server = socket.create_connection(
                            (conn.laddr.ip, conn.laddr.port)
                        )
                        server.sendall(json.dumps(arguments).encode())
                    break
    if not connections:
        app.run()
