import QtQuick 2.3
import QtGraphicalEffects 1.0
import Pyblish 0.1


BaseDelegate {
    id: root

    property bool hasLongMessage: msg.indexOf("\n") != -1 ? true : false
    property string shortMessage: msg.split("\n")[0]
    property string longMessage: msg

    expandable: hasLongMessage

    height: bodyItem.__height + 5

    property var levelColors: {
        "DEBUG":      Qt.lighter("steelblue", 1.3),
        "INFO":       Qt.lighter("steelblue", 1.5),
        "WARNING":    Qt.lighter("red", 1.6),
        "ERROR":      Qt.lighter("red", 1.4),
        "CRITICAL":   Qt.lighter("red", 1.2)
    }

    color: levelColors[levelname]

    body: Row {
        id: content

        property real __height: mask.height

        spacing: 10

        Item {
            width: mask.width
            height: mask.height

            Rectangle {
                id: rect

                color: root.color
                anchors.fill: parent

                visible: false
            }

            Icon {
                id: mask

                name: "log-white-16x16"

                visible: false
            }

            OpacityMask {
                id: opacityMask
                anchors.fill: parent
                source: rect
                maskSource: mask
            }
        }

        Label {
            id: messageLabel

            text: expanded ? longMessage : shortMessage
            elide: Text.ElideRight
            wrapMode: expanded ? Text.WordWrap : Text.NoWrap

            width: root.width - mask.paintedWidth - spacing
        }
    }
}
