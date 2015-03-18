import QtQuick 2.3
import Pyblish 0.1


Item {
    id: overview

    property string __lastPlugin

    signal instanceDoubleClicked(int index)
    signal pluginDoubleClicked(int index)

    states: [
        State {
            name: "publishing"
        },

        State {
            name: "finished"
        }
    ]

    onStateChanged: {
        if (state === "publishing") {
            terminal.clear()
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
        anchors.bottomMargin: 0

        width: parent.width - 10

        elevation: -1

        Row {
            visible: tabBar.currentIndex == 0

            anchors.fill: parent
            anchors.margins: parent.margins

            List {
                model: app.instanceModel
                width: parent.width / 2
                height: parent.height

                section.property: "family"

                onItemClicked: app.toggleInstance(index)
                onItemDoubleClicked: overview.instanceDoubleClicked(index)
            }

            List {
                model: app.pluginModel
                width: parent.width / 2
                height: parent.height

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

        mode: overview.state == "publishing" ? 1 : overview.state == "finished" ? 2 : 0

        width: parent.width
        anchors.bottom: parent.bottom

        onPublish: {
            overview.state = "publishing"
            app.publish()
        }

        onReset: {
            overview.state = ""
            setMessage("Resetting..")
            terminal.clear()
            app.reset()
        }

        onStop: {
            overview.state = "finished"
            setMessage("Stopping..")
            app.stop()
        }

        onSave: {
            app.save()
        }
    }

    Connections {
        target: app

        /*
         * Print results of publish in Terminal
        */
        onProcessed: {
            // app.log.info(JSON.stringify(data))
            if (typeof data.instance === "undefined")
                return

            if (overview.__lastPlugin != data.plugin) {
                terminal.echo("<p>-----------------------------------------------</p>")
                terminal.echo()
                terminal.echo("<b style='font-size: 15px'>" + data.plugin + "</b>")

                overview.__lastPlugin = data.plugin
            }

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
                terminal.echo("<p>%1</p".arg(record.levelname + " - " + record.msg))
            })


            if (data.error) {
                /*
                 * Available fields
                 *  .traceback[0] (filename)
                 *  .traceback[1] (lineNo)
                 *  .traceback[2] (funcName)
                 *  .traceback[3] (code)
                 *  .message
                */
                terminal.echo()
                terminal.echo("<p style='color: rgb(255, 100, 100)'>Validation failed</p>")
                terminal.echo("<p style='color: rgb(255, 100, 100)'>%1</p>".arg(data.error.message))
                // terminal.echo("    File: " + data.error.traceback[0])
                // terminal.echo("    Line Number: " + data.error.traceback[1])
                // terminal.echo("    Function Name: " + data.error.traceback[2])
            }

            // terminal.echo("-----------------------------------------------")
            terminal.echo()  // Newline
        }

        onFinished: {
            overview.state = "finished"
            setMessage("Finished")
        }

        onError: {
            setMessage(message)
        }

        onInfo: {
            terminal.echo(message)
        }

        onSaved: {
            setMessage("Saved")
        }
    }

    Component.onCompleted: {
        terminal.clear()
    }
}