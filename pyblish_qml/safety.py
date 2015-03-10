import os
import sys
import json
import ConfigParser

cwd = os.path.dirname(sys.executable)
qtconf_path = os.path.join(cwd, "qt.conf")

stats = dict(
    executable=sys.executable,
    qtconfpath=None,
    qtconf=None,
    x64=False
)


def validate():
    if not sys.maxsize > 2**32:
        raise Exception("32-bit interpreter detected; must be running "
                        "Python x86-64\nE.g. https://www.python.org/ftp"
                        "/python/2.7.9/python-2.7.9.amd64.msi")
    else:
        stats["x64"] = True

    try:
        __import__("PyQt5")
    except:
        raise Exception("PyQt5 not found")

    try:
        __import__("pyblish")
        __import__("pyblish_qml")
        __import__("pyblish_endpoint")
    except:
        raise Exception("Pyblish Suite not found")

    if not os.path.isfile(qtconf_path):
        raise Exception("No qt.conf found at %s" % cwd)
    else:
        stats["qtconfpath"] = qtconf_path

    config = ConfigParser.ConfigParser()
    config.read(qtconf_path)
    stats["qtconf"] = json.dumps(config._sections)

    try:
        prefix_dir = config.get("Paths", "prefix")
        binaries_dir = config.get("Paths", "binaries")

        assert binaries_dir == prefix_dir
        assert os.path.isdir(prefix_dir)
        assert prefix_dir.endswith("PyQt5")
        assert "designer.exe" in os.listdir(prefix_dir)

    except:
        raise Exception("qt.conf misconfigured")

    return """Success!

{exe} is well suited to run Pyblish QML.

To test:
    {exe} -m pyblish_qml
""".format(exe=sys.executable)


if __name__ == '__main__':
    print validate()
