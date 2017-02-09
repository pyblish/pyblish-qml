
### Pyblish QML

The Pyblish QML project provides a graphical frontend to [Pyblish](http://pyblish.com).

[![Build Status](https://travis-ci.org/pyblish/pyblish-qml.svg?branch=master)](https://travis-ci.org/pyblish/pyblish-qml)

![](https://cloud.githubusercontent.com/assets/2152766/16178722/30c3d28c-3648-11e6-8361-84f04113af4b.gif)

<br>
<br>
<br>

### Requirements

The Pyblish QML **client** depends on [pyblish-base](https://github.com/pyblish/pyblish-base) and Python 2 or 3, whereas the **server** requires PyQt5.

- **Any platform** 
 
 PyQt5 is available on PyPI, but only for Python 3.5. For any other distribution, see below.

 ```bash
$ pip install PyQt5
```

- **Windows**

 On Windows, you may download and install the binary distribution from the [Riverbank Software website](https://www.riverbankcomputing.com/software/pyqt/download5).

- **Debian**

 Like most Linux distribution, Debian will have PyQt5 available via its native package manager.

 ```bash
$ apt-get install python3-pyqt5 python3-pyqt5.qtquick
```

 See `yum` for Red Hat based distributions.

- **MacOS**

 Finally, brew provides a pre-compiled distribution for Python 3 as well.

 ```bash
$ brew install pyqt5
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

### Documentation

Below is the current and full documentation of QML.

- [Data](#data)
- [Perspective](#perspective)
- [Visualise order of operation](#order)
- [Optional plugins](#optional)
- [Plug-in documentation](#plug-in-documentation)
- [Log messages](#log-messages)
- [Exception messages](#exception-messages)

<br>

#### Data

Some data within each Instance and Context are special to QML.

| Member    | Applies to       | Behavior
|:----------|:-----------------|:-------------------
| `publish` | Instance         | The on/off state of the toggle.
| `label`   | Context/Instance | Draw this instead of an instance's `name`

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
import pyblish_qml
pyblish_qml.settings.WindowTitle = "My Title"
pyblish_qml.settings.WindowSize = (430, 600)
pyblish_qml.settings.ContextLabel = "The World"
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

### Usage

Run Pyblish QML from any terminal, then show it from your favourite digital content creation software.

**Server**

```bash
# From any terminal
$ python -m pyblish_qml
```

**Client**

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

It uses the standard [`xmlrpc`](https://docs.python.org/2/library/xmlrpclib.html) library and default to responding to calls via port number `9090`.

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

### Differences to [Pyblish Lite](https://github.com/mottosso/pyblish-lite)

Pyblish QML fills the same gap as Pyblish Lite, with a few notable differences.

**Pros**

- Asynchronous operation - use the GUI during intense processing
- Faster startup time - it's running before you are
- Smoother visuals - animations galore
- Inspect individual items - tens of instances, hundreds of plug-ins? no problem
- Filter terminal via keyword search - thousands of log entries? no problem

**Cons**

- Requires PyQt5 (and either Python 2 or 3)
- Supports only one publish at a time, for one logged on user at a time ([#199](https://github.com/pyblish/pyblish-qml/issues/199))

Development wise, Pyblish QML is written in.. you guessed it, QML. Whereas Pyblish Lite is written using classig widgets. QML is a new graphical user interface language for OpenGL developed by the same group, Qt.

<br>
<br>
<br>

### Common Problems

Due to the inherent complexity of the client/server-style implementation of this project, some of the below problems are likely to puzzle you at first.

![image](https://cloud.githubusercontent.com/assets/2152766/16816779/882b6880-4937-11e6-842a-0becb69e5855.png)

Search the [Issues](https://github.com/pyblish/pyblish-qml/issues/new) section, if nothing is found feel free to open your own issue or [report a problem on the forums](http://forums.pyblish.com).

<br>
<br>
<br>

### Testing

Tests are automatically run at each commit to GitHub via Travis-CI. You can run these tests locally via Docker too.

```bash
$ git clone https://github.com/pyblish/pyblish-qml.git
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
