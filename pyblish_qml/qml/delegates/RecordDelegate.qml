import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    property string shortMessage: msg.split("\n")[0]
    property string longMessage: msg

    expandable: true

    height: bodyItem.height + 5

    property var levels: {
        "DEBUG":  {
            "color": Qt.lighter("steelblue", 1.3),
            "icon": "log-debug-16x16"
        },
        "INFO": {
            "color": Qt.lighter("steelblue", 1.5),
            "icon": "log-info-16x16"
        },
        "WARNING": {
            "color": Qt.lighter("red", 1.6),
            "icon": "log-warning-16x16"
        },
        "ERROR": {
            "color": Qt.lighter("red", 1.4),
            "icon": "log-error-16x16"
        },
        "CRITICAL": {
            "color": Qt.lighter("red", 1.2),
            "icon": "log-critical-16x16"
        }
    }

    color: levels[levelname].color

    body: Row {
        // property real __height: Math.max(mask.height, messageLabel.paintedHeight, 
        property alias icon: mask.name

        spacing: 10

        Icon {
            id: mask
            name: levels[levelname].icon
        }

        Column {
            spacing: 10

            Label {
                id: messageLabel

                text: expanded ? longMessage : shortMessage
                elide: Text.ElideRight
                wrapMode: expanded ? Text.WordWrap : Text.NoWrap

                width: root.width -
                       mask.paintedWidth -
                       spacing -
                       root.toggle.width -
                       10
            }

            Column {
                visible: expanded

                Repeater {

                    model: [
                        {
                            "key": "Levelname",
                            "value": levelname
                        },
                        {
                            "key": "Object",
                            "value": name
                        },
                        {
                            "key": "Filename",
                            "value": filename
                        },
                        {
                            "key": "Path",
                            "value": pathname
                        },
                        {
                            "key": "Line number",
                            "value": lineno
                        },
                        {
                            "key": "Function name",
                            "value": funcName
                        },
                        {
                            "key": "Thread",
                            "value": threadName
                        },
                        {
                            "key": "Milliseconds",
                            "value": msecs
                        },
                    ]

                    Row {
                        spacing: 5
                        opacity: 0.5

                        Label {
                            text: modelData.key
                            backgroundColor: Theme.alpha("white", 0.1)
                        }

                        Label {
                            text: typeof modelData.value != "object" ? modelData.value : JSON.stringify(modelData.value)
                        }
                    }
                }
            }
        }
    }
}
