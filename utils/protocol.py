import os
import sys
from pathlib import Path


def set_protocol():
    if not getattr(sys, "frozen", False):
        return
    if os.name == "nt":
        import winreg

        executable = Path(sys.executable)
        protocol = "rtt"
        protocol_path = r"SOFTWARE\Classes\{0}".format(protocol)
        command = r'"{0}" "%1"'.format(executable)
        with winreg.CreateKey(winreg.HKEY_CURRENT_USER, protocol_path) as key:
            winreg.SetValue(key, None, winreg.REG_SZ, "")
            winreg.SetValueEx(key, "URL Protocol", 0, winreg.REG_SZ, "")
            with winreg.CreateKey(key, r"shell\open\command") as command_key:
                winreg.SetValue(command_key, None, winreg.REG_SZ, command)
