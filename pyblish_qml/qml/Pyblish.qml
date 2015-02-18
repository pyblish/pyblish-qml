import QtQuick 2.3
import Pyblish 0.1


Item {
    id: pyblish

    states: [
        State {
            name: "publishing"

            PropertyChanges {
                target: footer

                mode: 1
            }
        }
    ]

    onStateChanged: {
        if (state === "publishing") {
            terminal.clear()
            terminal.echo("Logging started " + Date() + "\n")
        }
    }

    function setMessage(message) {
        footer.message.text = message
        footer.message.animation.restart()
        footer.message.animation.start()
        app.log.info(message)
    }

    TabBar {
        id: tabBar

        anchors.top: parent.top

        tabs: [
            {
                text: "",
                icon: "logo-white"
            },
            "Terminal"
        ]
    }

    TabView {
        id: tabView

        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: tabBar.bottom
        anchors.bottom: footer.top

        currentIndex: tabBar.currentIndex

        model: tabs
    }

    VisualItemModel {
        id: tabs

        View {
            width: tabView.width
            height: tabView.height

            style: "inwards"

            Row {
                anchors.fill: parent
                anchors.margins: parent.margins

                List {
                    model: app.instanceModel

                    section.property: "family"

                    onItemClicked: {
                        app.toggleInstance(index)
                    }
                }

                List {
                    model: app.pluginModel

                    section.property: "type"

                    onItemClicked: {
                        app.togglePlugin(index)
                    }
                }
            }
        }

        View {
            width: tabView.width
            height: tabView.height
            
            Terminal {
                id: terminal
                anchors.fill: parent
            }
        }
    }

    Footer {
        id: footer
        width: parent.width
        anchors.bottom: parent.bottom

        onPublish: {
            pyblish.state = "publishing"
            app.publish()
        }

        onReset: {
            setMessage("Resetting..")
            app.reset()
        }

        onStop: {
            setMessage("Stopping..")
            app.stop()
        }
    }

    Connections {
        target: app

        /*
         * Print results of publish in Terminal
        */
        onProcessed: {
            if (typeof data.instance === "undefined")
                return

            terminal.echo("<b>" + data.plugin + "</b>")
            
            terminal.echo("    -----------------------------------------------")
            
            data.records.forEach(function (record) {
                /* 
                 * Available fields
                 *  .args
                 *  .created
                 *  .filename
                 *  .funcName
                 *  .levelname
                 *  .levelno
                 *  .lineno
                 *  .message
                 *  .module
                 *  .msecs
                 *  .msg
                 *  .name
                 *  .pathname
                 *  .process
                 *  .processName
                 *  .relativeCreated
                 *  .thread
                 *  .threadName
                */
                terminal.echo("    " + record.levelname + " - " + record.msg)
            })

            terminal.echo("    -----------------------------------------------")

            if (data.error) {
                /*
                 * Available fields
                 *  .traceback[0] (filename)
                 *  .traceback[1] (lineNo)
                 *  .traceback[2] (funcName)
                 *  .traceback[3] (code)
                 *  .message
                */
                terminal.echo("    FAIL: " + data.error.message)
                terminal.echo("        filename: " + data.error.traceback[0])
                terminal.echo("        lineNo: " + data.error.traceback[1])
                terminal.echo("        funcName: " + data.error.traceback[2])
            }

            terminal.echo()  // Newline
        }

        onFinished: {
            pyblish.state = "default"
        }

        onError: {
            setMessage(message)
        }

        onInfo:
            terminal.echo(message)
    }

    Component.onCompleted: {
        Object.keys(app.system).sort().forEach(function (key) {
            terminal.echo(key + ": " + app.system[key]);
        });
    }
}