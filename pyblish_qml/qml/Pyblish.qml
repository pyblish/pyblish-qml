import QtQuick 2.3
import "."


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
            terminal.text = "Logging started " + Date() + "\n"
        }
    }

    function setMessage(message) {
        footer.message.text = message
        footer.message.animation.restart()
        footer.message.animation.start()
        app.log.info(message)
    }

    Column {
        anchors.fill: parent

        Tabs {
            id: tabbar

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
            height: parent.height
            width: parent.width

            currentIndex: tabbar.currentIndex

            model: tabs
        }

        VisualItemModel {
            id: tabs

            Box {
                width: tabView.width
                height: tabView.height

                style: "inwards"

                Row {
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

            Box {
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