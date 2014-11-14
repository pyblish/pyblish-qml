
import subprocess

CREATE_NO_WINDOW = 0x08000000


def run(host, port=6000, console=True, async=False):
    if async:
        return _run_async(host, port, console)

    import pyblish_qml.app
    return pyblish_qml.app.run(host, port)


def _run_async(host, port, console):
    kwargs = {}
    if console is False:
        kwargs["creationflags"] = CREATE_NO_WINDOW

    proc = subprocess.Popen(["python", "-m", "pyblish_qml",
                            "--host", host,
                            "--port", str(port)], **kwargs)

    return proc
