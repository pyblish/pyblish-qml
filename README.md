
![](https://cloud.githubusercontent.com/assets/2152766/16178722/30c3d28c-3648-11e6-8361-84f04113af4b.gif)

[![Build Status](https://travis-ci.org/pyblish/pyblish-qml.svg?branch=master)](https://travis-ci.org/pyblish/pyblish-qml)

### Pyblish QML

The Pyblish QML project provides a graphical frontend to [Pyblish](http://pyblish.com).

<br>
<br>
<br>

### Installation

Requires [pyblish-base](https://github.com/pyblish/pyblish-base), Python 3 and PyQt5.

```bash
$ pip install pyblish-qml
```

Test out the installation with..

```bash
$ python -m pyblish_qml --demo
```

<br>
<br>
<br>

### Usage

Run Pyblish QML from any terminal, then show it from your favourite digital content creation software.

**Start**

```bash
# From any terminal
$ python -m pyblish_qml
```

**Show**

```python
# From your favourite DCC
import pyblish_qml
pyblish_qml.show()
```

<br>
<br>
<br>

### Under the Hood

Pyblish QML runs as an independent process on your computer, and communicates with your host via interprocess communication through remote-procedure calls (RPC).

It uses the standard [`xmlrpc`]() library and default to responding to calls via port number 9090.

```python
>>> from xmlrpclib import ServerProxy
>>> proxy = ServerProxy("http://127.0.0.1:9090", allow_none=True)
>>> proxy.ping()
{'message': 'Hello, whomever you are'}
```

When you show Pyblish QML from within a host, you are effectively making an IPC connection and calling `show` with parameters relative the currently running process.

```python
>>> proxy.show(9001, {})
# GUI appears
```

The `9001` refers to the port number through which Pyblish QML may reach whomever is asking it to show. When calling `pyblish_qml.show()`, a listener is automatically started for you to receive calls from Pyblish QML; unless one is already running.

```python
def show():
    if not listener_started:
        start_listener()

    proxy.show()
```

You can manually start such a listener by calling..

```python
import pyblish_qml
pyblish_qml.install()
```

This needs only happen once. To shutdown the listener, you may call..

```python
pyblish_qml.uninstall()
```

<br>
<br>
<br>

### Testing

Tests are automatically run at each commit to GitHub via Travis-CI. You can run these tests locally via Docker too.

```bash
$ git clone https://github.com/mottosso/pyblish-qml.git
$ cd pyblish-qml
$ docker build -t pyblish/pyblish-qml .
$ docker run --rm -v $(pwd):/pyblish-qml pyblish/pyblish-qml
# Doctest: pyblish_qml.models.Item ... ok
# Doctest: pyblish_qml.util.ItemList ... ok
# Reset works ... ok
# Publishing works ... ok
# ...
# util.chain works with lambdas ... ok
# 
# ----------------------------------------------------------------------
# Ran 20 tests in 1.430s
# 
# OK
```
