[![Build Status](https://travis-ci.org/pyblish/pyblish-qml.svg?branch=master)](https://travis-ci.org/pyblish/pyblish-qml)

![image](https://cloud.githubusercontent.com/assets/2152766/5247020/d8b8281c-7966-11e4-8452-226235022d56.png)

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
$ python -m pyblish_qml --debug
```

<br>
<br>
<br>

### Usage

Run Pyblish QML from any terminal, then emit a signal from your favourite digital content creation software.

**Start Client**

```bash
# From any terminal
$ python -m pyblish_qml
```

**Start Server**

```python
# From your favourite DCC
import pyblish_qml
pyblish_qml.listen()
```
