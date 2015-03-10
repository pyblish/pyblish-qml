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
    """Validate compatibility with environment and Pyblish QML

    Raises an exception in the event the system is not compatible.

    """

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


"""Run Pyblish in a clean environment

Usage:
    $ generate.py
    $ run.bat

"""


def generate_safemode_windows():
    """Produce batch file to run QML in safe-mode

    Usage:
        $ python -c "import safety;safety.generate_safemode_windows()"
        $ run.bat

    """

    try:
        import pyblish
        import pyblish_qml
        import pyblish_endpoint
        import PyQt5

    except ImportError:
        print "Run this in a terminal with access to the Pyblish libraries and PyQt5"
        return

    template = r"""@echo off

    :: Clear all environment variables

    @echo off
    if exist ".\backup_env.bat" del ".\backup_env.bat"
    for /f "tokens=1* delims==" %%a in ('set') do (
    echo set %%a=%%b>> .\backup_env.bat
    set %%a=
    )

    :: Set only the bare essentials

    set PATH={PyQt5}
    set PATH=%PATH%;{python}
    set PYTHONPATH={pyblish}
    set PYTHONPATH=%PYTHONPATH%;{pyblish_qml}
    set PYTHONPATH=%PYTHONPATH%;{pyblish_endpoint}
    set PYTHONPATH=%PYTHONPATH%;{PyQt5}

    set SystemRoot=C:\Windows

    :: Run Pyblish

    python -m pyblish_qml

    :: Restore environment
    backup_env.bat

    """

    values = {}
    for lib in (pyblish, pyblish_qml, pyblish_endpoint, PyQt5):
        values[lib.__name__] = os.path.dirname(os.path.dirname(lib.__file__))

    values["python"] = os.path.dirname(sys.executable)

    with open("run.bat", "w") as f:
        print "Writing %s" % template.format(**values)
        f.write(template.format(**values))


if __name__ == '__main__':
    print validate()
