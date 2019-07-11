
### Pyblish QML

The Pyblish QML project provides a graphical frontend to [Pyblish](http://pyblish.com).

[![Build Status](https://travis-ci.org/pyblish/pyblish-qml.svg?branch=master)](https://travis-ci.org/pyblish/pyblish-qml) [![](https://badge.fury.io/py/pyblish-qml.svg)](https://pypi.org/project/pyblish-qml/)


![](https://cloud.githubusercontent.com/assets/2152766/16178722/30c3d28c-3648-11e6-8361-84f04113af4b.gif)

<br>
<br>
<br>

### Requirements

Pyblish QML works with..

- Standalone
- Maya 2013+
- Nuke 8+
- Houdini 11+
- Blender 2.79-2.80+

..and requires an external Python (2 or 3) install with PyQt 5.6+ available.

- Pyblish 1.2.1 or higher
- [Python 3.5 any platform](../../wiki/Python-3.5-Any-Platform)
- [Python 2.7 on Windows](../../wiki/Python-2.7-Windows)
- [Python 2.7 on CentOS 7](../../wiki/Python-2.7-CentOS)
- [Python 2.7 on Ubuntu 14.10](../../wiki/Python-2.7-Ubuntu)
- [Python 2.7 on MacOS](../../wiki/Python-2.7-MacOS)

Before use, point to your Python executable like this.

```bash
$ set PYBLISH_QML_PYTHON_EXECUTABLE=c:\python27\python.exe
```

This assumes the Python distribution has access to PyQt5 via e.g. `python -c "import PyQt5"`. If not, you may point to the directory containing it like this.

```bash
$ set PYBLISH_QML_PYQT5=c:\path\to\pyqt
```

<br>
<br>
<br>

### Installation

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

In any of the supported hosts, call show().

```python
import pyblish_qml
pyblish_qml.show()
```

<br>

First you need to tell QML where Python and PyQt5 is.

```python
from pyblish_qml import api, show

# Tell QML about dependencies
api.register_python_executable("C:/Python27/python.exe")
api.register_pyqt5("C:/modules/python-qt5")

show()
```

Alternatively, you may use environment variables instead.

```bash
$ set PYBLISH_QML_PYTHON_EXECUTABLE=c:\python27\python.exe
$ set PYBLISH_QML_PYQT5=c:\modules\python-qt5
$ maya  # for example..
```

> Keep in mind that you don't have to register PyQt5 unless the Python executable you register isn't able to find it on its own. Also keep in mind that the directory you need to register is the parent directory of the `PyQt5` Python package.

Either way, once QML is aware of where dependencies are, you may register it with `pyblish-base` and have it appear automatically in file-menus of software, like with `pyblish-qml`.

```python
from pyblish import api
api.register_gui("pyblish_qml")
```

See [pyblish-maya](https://github.com/pyblish/pyblish-maya#usage) for an example.

**Additional Environment Variables**

- `PYBLISH_QML_MODAL=1` Block interactions to parent process, useful for headless publishing where you expect a process to remain alive for as long as QML is. Without this, Pyblish is at the mercy of the parent process, e.g. `mayapy` which quits at the first sign of EOF.

<br>
<br>
<br>

### Documentation

Below is the current and full documentation of QML.

- [Supported hosts](#supported-hosts)
- [Data](#data)
- [Perspective](#perspective)
- [Visualise order of operation](#order)
- [Optional plugins](#optional)
- [Plug-in documentation](#plug-in-documentation)
- [Log messages](#log-messages)
- [Exception messages](#exception-messages)

<br>

#### Supported Hosts

These are the hosts automatically recognised by pyblish-qml.

- Maya
- Nuke
- Houdini
- Hiero

<br>

#### Data

Some data within each Instance and Context are special to QML.

| Member    | Applies to       | Behavior
|:----------|:-----------------|:-------------------
| `publish` | Instance         | The on/off state of the toggle.
| `label`   | Context/Instance | Draw this instead of an instance's `name`
| `comment` | Context          | Display and edit comment in GUI

<br>

#### Perspective

Dive into any item to find a curated list of data related to a particular item.

![](https://cloud.githubusercontent.com/assets/2152766/8282801/0955d220-18eb-11e5-985e-d7c55ea37f40.gif)

<br>

#### Order

The order in which items are listed in the interface is a representation of how they are about to be processed. The top-most item processes first, and the bottom-most item processes last.

You can control the order by modifying the [order attribute][order].

[order]: https://api.pyblish.com/pages/Plugin.order.html

<br>


#### Optional

Plug-ins can be made optional by adding a particular attribute to your plug-ins.

```python
class MyPlugin(...):
   optional = True
```

When a plug-in is optional, an artist may choose whether or not it should perform any processing.

<br>


#### Plug-in documentation

![image](https://cloud.githubusercontent.com/assets/2152766/6870922/0e201380-d497-11e4-9dcf-2c361f23a008.png)

Provide your users with thorough information of what to expect of a plug-in.

Pyblish QML visualises documentation per-plugin, here are some best practices for writing it along with technical information about how the data is parsed before being displayed.

**Purpose**

The following are some guidelines to adhere to when writing documentation for your plug-in, but are in no way mandatory nor have any effect on the operation of Pyblish or Pyblish QML.

1. Provide a general understanding of what the plug-in is doing.
2. In case of a validator, propose general solutions and best-practices for how to avoid failing.
3. Do not provide specific solutions; save those for [Exception messages](#exception-messages).

**Behaviour**

Documentation is taken from the `__doc__` member of your plug-in class.

```python
class MyValidator(...):
   """General description

   Longer description here.

   """
```

As per PEP08, the first line of the above docstring is treated as a *summary* of the below description and used in the GUI right after drawing the name of the plug-in.

![image](https://cloud.githubusercontent.com/assets/2152766/6869940/d7309058-d490-11e4-81d7-288201a5abba.png)

The longer portion is then shown when expanded.

![image](https://cloud.githubusercontent.com/assets/2152766/6870753/0488004a-d496-11e4-9c71-7d517be1d987.png)

If a line should be too long to display in the GUI, the end of it is elided.

**Parsing**

Before showing the docstring, it is parsed. Parsing is currently very straightforward and operates on two rules.

1. Remove all newlines
2. Keep paragraphs

This happens so as to ensure that the maximum amount of space is used in the GUI and to get rid of the leading tabs present in any docstring.

Which means that this...

```python
class MyValidator(...):
   """General description

   Longer description
   here.

   """
```

translates into..

```python
General description

Longer description here.
```

**Caveats**

As a side-effect of the above two rules, you cannot make lists or other entries that depend on newlines.

<br>
<br>

#### Log messages

Provide users with information about what happens during the processing of a plug-in.

Logging uses the Python standard library `logging` module and is visualised graphically by its 5 levels of severity.

1. Debug
2. Info
3. Warning
4. Error
5. Critical

Each produced via it's corresponding call to `self.log` within a plug-in.

```python
class MyValidator(...):
    ...
    def process(...):
        self.log.debug("e=mc^2")
        self.log.info("Processing instance..")
        self.log.warning("Something may be wrong..")
        self.log.error("Something's *definitely* wrong!")
        self.log.critical("Call the president!")
```

Each level is then represented by its unique color, starting from Blue moving into Red.

**Details**

A log message may be short or span multiple lines. Only the first line is visualised unless an item is expanded. Once expanded, similar rules apply to parsing as the parsing of docstring ([See Plug-in Documentation](#plug-in-documentation) for more information.

- Short version

![image](https://cloud.githubusercontent.com/assets/2152766/6871306/93128bac-d499-11e4-9580-3e14b634e061.png)

- Expanded version

![image](https://cloud.githubusercontent.com/assets/2152766/6871329/b0722da6-d499-11e4-9e0c-d97af68204db.png)

**Example**

![image](https://cloud.githubusercontent.com/assets/2152766/6871170/b72ae512-d498-11e4-9af4-669f3cfa9013.png)

<br>
<br>

### Exception messages

Provide users with specifics about why a plug-in failed.

Exception messages are logged when exceptions are raised by plug-ins and are designed for describing the exact resort to take when plug-ins fail.

Contrary to [Plug-in Documentation](#plug-in-documentation), Exception Messages may get very specific about a problem, such as naming items in a host relevant to the error, or point to a particular portion of the documentation.

**Behaviour**

As with [Log Messages](#log-messages), the first line of the message is shown by default, subsequent lines are hidden until expanded and follow the same formatting rules as [Plug-in Documentation](#plug-in-documentation).

```python
raise ValidationError("""This is a long message

And this will appear once expanded.

""")
```

> Pro tip: It's considered good practice to include as much information as is needed here, this is where users are meant to go for specifics about what to do about a particular problem.

**Example**

![](https://cloud.githubusercontent.com/assets/2152766/6871170/b72ae512-d498-11e4-9af4-669f3cfa9013.png)

<br>
<br>

#### Settings

![](https://cloud.githubusercontent.com/assets/2152766/8280569/5d53b244-18d6-11e5-8a9a-4b51ad9cdbb8.gif)

Customise Context label and Window title.

```python
from pyblish_qml import settings
settings.WindowTitle = "My Title"
settings.WindowSize = (430, 600)
settings.WindowPosition = (100, 100)
settings.ContextLabel = "The World"
settings.HiddenSections = ["Collect"]
```

Each setting is applied when the GUI is shown, which means you can change them any time before then, including between subsequent runs.

Alternatively, set context label during processing.

```python
class CollectContextLabel(pyblish.api.ContextPlugin):
  order = pyblish.api.CollectorOrder

  def process(self, context):
    context.data["label"] = "The World"
```

The GUI will read the current label after having processed *all* collectors. Any change after Collection will not be visible in the GUI.

<br>
<br>
<br>

### Differences to [Pyblish Lite](https://github.com/mottosso/pyblish-lite)

Pyblish QML fills the same gap as Pyblish Lite, with a few notable differences.

**Pros**

- Asynchronous operation - use the GUI during intense processing
- Smoother visuals - animations galore
- Inspect individual items - tens of instances, hundreds of plug-ins? no problem
- Filter terminal via keyword search - thousands of log entries? no problem

**Cons**

- Requires PyQt5 (and either Python 2 or 3)

Development wise, Pyblish QML is written in.. you guessed it, QML. Whereas Pyblish Lite is written using classic widgets. QML is a new graphical user interface language for OpenGL developed by the same group, Qt.

<br>
<br>
<br>

### Testing

Tests are automatically run at each commit to GitHub via Travis-CI. You can run these tests locally via Docker too.

```bash
$ git clone https://github.com/pyblish/pyblish-qml.git
$ cd pyblish-qml
$ . build_docker.sh  # Only needed once
$ . test_docker.sh
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

If you don't have Docker available you can test with these commands, for both Python 2 and Python 3:

```bash
$ cd pyblish-qml
$ python -m nose --verbose --with-doctest --exe --exclude=vendor
```
