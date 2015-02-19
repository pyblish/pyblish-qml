import QtQuick 2.3
import Pyblish 0.1


Item {
    id: overview

    signal instanceDoubleClicked(int index)
    signal pluginDoubleClicked(int index)

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
        anchors.left: parent.left
        anchors.right: parent.right

        tabs: [
            {
                text: "",
                icon: "logo-white"
            },
            "Terminal"
        ]
    }

    View {
        id: tabView

        anchors.top: tabBar.bottom
        anchors.bottom: footer.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: tabView.margins

        width: parent.width - 10

        elevation: -1

        Row {
            visible: tabBar.currentIndex == 0

            anchors.fill: parent
            anchors.margins: parent.margins

            List {
                model: app.instanceModel
                width: parent.width / 2

                section.property: "family"

                onItemClicked: app.toggleInstance(index)
                onItemDoubleClicked: overview.instanceDoubleClicked(index)
            }

            List {
                model: app.pluginModel
                width: parent.width / 2

                section.property: "type"

                onItemClicked: app.togglePlugin(index)
                onItemDoubleClicked: overview.pluginDoubleClicked(index)
            }
        }

        Terminal {
            id: terminal
            anchors.fill: parent
            anchors.margins: parent.margins
            
            visible: tabBar.currentIndex == 1
        }
    }


    Footer {
        id: footer
        width: parent.width
        anchors.bottom: parent.bottom

        onPublish: {
            overview.state = "publishing"
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
            overview.state = "default"
            setMessage("Finished")
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