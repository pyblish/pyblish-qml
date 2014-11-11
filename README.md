### Pyblish QML

A GUI for [Pyblish][].

In a nutshell, this GUI communicates with hosts via inter-process communication using [Pyblish Endpoint][endpoint], which is a RESTful interface running independently on target hosts. An interface is tailored per host towards Endpoint, this GUI then communicates with Endpoint which then indirectly communicates with each host.

[Pyblish]: https://github.com/abstractfactory/pyblish
[endpoint]: https://github.com/pyblish/pyblish-endpoint

#### Usage

This GUI doesn't do much yet, but you are free to install it and play around; just make sure you understand the [limitations](#limitations)

![](https://cloud.githubusercontent.com/assets/2152766/4982100/ccc3dcf2-690f-11e4-91b5-f4fd71e4bc50.gif)

**Installation**

To get started, you will need a host integration, such as [Pyblish for Maya][maya], along with [Pyblish Endpoint][endpoint]. Once installed, follow these instructions.

1. Clone this repository

 ```bash
 $ git clone https://github.com/pyblish/pyblish-qml.git
 $ cd pyblish-qml
 ```

2. Install QML 5.3
    
 Either by installing Qt 5.3

 - http://qt-project.org/downloads

 **OR**

 Install the [python-qt5][qt5] Python package, available for Windows only.

 ```bash
 $ pip install python-qt5
 ```

3. Ensure QML is available on your PATH.

 ```bash
 # This should present you with a browser dialog.
 $ qmlscene
 ```

Hosts will automatically pick up upon the installation of Pyblish QML, assuming you've also got Pyblish Endpoint installed. Look for an option to launch Pyblish QML in your host.

[qt5]: https://github.com/pyqt/python-qt5
[maya]: https://github.com/abstractfactory/pyblish-maya

#### Limitations

At this point, Pyblish QML:

- Only runs on [Maya][maya].
- Only runs on the first instantiated process.
- Does NOT provide any feedback; except a completion message.
- Does NOT support partial publishing; although the GUI suggests it.
- Takes 2 seconds to start.


#### Integrations

To integrate this GUI into a host of your choice, head over the the [Pyblish Endpoint documentation][endpoint] for more information.