import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    property string shortMessage: item.message.split("\n")[0]
    property string longMessage: item.message

    expandable: true

    height: {
        if (loader.status == Loader.Ready)
            return loader.item.height + 5
        return 0
    }

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

    color: levels[item.levelname].color

    body: Row {
        property alias icon: mask.name

        spacing: 10

        Icon {
            id: mask
            name: levels[item.levelname].icon
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
                            "value": item.levelname
                        },
                        {
                            "key": "Object",
                            "value": item.name
                        },
                        {
                            "key": "Filename",
                            "value": item.filename
                        },
                        {
                            "key": "Path",
                            "value": item.pathname
                        },
                        {
                            "key": "Line number",
                            "value": item.lineno
                        },
                        {
                            "key": "Function name",
                            "value": item.funcName
                        },
                        {
                            "key": "Thread",
                            "value": item.threadName
                        },
                        {
                            "key": "Milliseconds",
                            "value": item.msecs
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
