import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    property bool hasLongMessage: msg.indexOf("\n") != -1 ? true : false
    property string shortMessage: msg.split("\n")[0]
    property string longMessage: msg

    expandable: hasLongMessage

    height: bodyItem.__height

    property var levelColors: {
        "DEBUG": Qt.lighter("steelblue", 1.3),
        "INFO": Qt.lighter("steelblue", 1.5),
        "WARNING": Qt.lighter("red", 1.6),
        "ERROR": Qt.lighter("red", 1.4),
        "CRITICAL": Qt.lighter("red", 1.2)
    }

    color: levelColors[levelname]

    body: Row {
        id: content

        property real __height: messageLabel.paintedHeight

        spacing: 10

        Label {
            id: levelLabel

            text: levelname
            color: root.color
            backgroundColor: Theme.alpha(root.color, 0.1)
        }

        Label {
            id: messageLabel

            text: expanded ? longMessage : shortMessage
            elide: Text.ElideRight
            wrapMode: expanded ? Text.WordWrap : Text.NoWrap

            width: root.width - levelLabel.paintedWidth - spacing
        }
    }
}
