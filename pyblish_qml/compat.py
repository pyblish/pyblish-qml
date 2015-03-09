import os


def windows_taskbar_compat():
    """Enable icon and taskbar grouping for Windows 7+"""

    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"pyblish.qml")


def main():
    if os.name == "nt":
        windows_taskbar_compat()
