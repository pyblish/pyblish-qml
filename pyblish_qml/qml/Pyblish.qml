import QtQuick 2.3
import "."


Item {
    id: pyblish
    state: header.state

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
        if (state === "publishing")
            terminal.text = "Logging started " + Date() + "\n"

    }

    function setMessage(message) {
        footer.message.text = message
        footer.message.animation.restart()
        footer.message.animation.start()
        app.log.info(message)
    }

    Column {
        anchors.fill: parent

        Header {
            id: header
            state: "overviewTab" // Default state
            width: parent.width
        }

        Box {
            id: body

            outwards: false
            width: parent.width
            height: parent.height - header.height - footer.height

            Item {
                id: systemTab
                visible: header.state == "systemTab"
                anchors.fill: parent
                anchors.margins: Constant.marginMain

                TextEdit {
                    id: system
                    width: terminalFlick.width
                    height: terminalFlick.height
                    color: "white"
                    font.family: "Open Sans Semibold"
                    readOnly: true
                    wrapMode: TextEdit.Wrap
                    renderType: Text.NativeRendering

                    Component.onCompleted: {
                        var keys = Object.keys(app.system);
                        keys.sort();
                        keys.forEach(function (key) {
                            append(key + ": " + app.system[key]);
                        });
                    }
                }
            }

            Item {
                id: overviewTab
                anchors.fill: parent
                anchors.margins: Constant.marginMain
                visible: header.state == "overviewTab"

                List {
                    id: instancesList
                    model: app.instanceModel
                    anchors.fill: parent
                    anchors.rightMargin: parent.width / 2
                    section.property: "family"
                    hoverDirection: "left"

                    onItemToggled: {
                        app.toggleInstance(index)
                    }
                }

                List {
                    id: pluginsList

                    signal validate(string family)

                    model: app.pluginModel
                    anchors.fill: parent
                    anchors.leftMargin: parent.width / 2
                    section.property: "type"

                    onItemToggled: {
                        app.togglePlugin(index)
                    }
                }
            }

            Item {
                id: terminalTab
                visible: header.state == "terminalTab"
                anchors.fill: parent
                anchors.margins: Constant.marginMain

                Flickable {
                    id: terminalFlick
                    anchors.fill: parent
                    contentWidth: terminal.paintedWidth
                    contentHeight: terminal.paintedHeight
                    boundsBehavior: Flickable.DragOverBounds
                    flickableDirection: Flickable.VerticalFlick
                    clip: true


                    TextEdit {
                        id: terminal

                        function echo(line) {
                            terminalFlick.contentY = terminalFlick.contentHeight
                            terminal.append(line);
                        }

                        width: terminalTab.width
                        height: terminalTab.height
                        color: "white"
                        text: "Logging started " + Date();
                        font.family: "Consolas"
                        readOnly: true
                        wrapMode: TextEdit.Wrap
                        renderType: Text.NativeRendering
                        textFormat: TextEdit.AutoText
                    }
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
            // onPause: ..
            // onStop: ..
        }
    }

    Connections {
        target: app
        
        /*
         * Print results of publish in Terminal
        */
        onProcessed: {
            if (data.finished === true) {
                pyblish.state = "default"
                setMessage(data.message)
                return
            }

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

        onError: {
            setMessage(message)
        }

        onInfo:
            terminal.echo(message)
    }
}