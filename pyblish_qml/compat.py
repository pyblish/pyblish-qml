import os

if os.name == "nt":
    """Enable icon and taskbar grouping for Windows 7+"""
    import ctypes
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(u"pyblish.qml")
