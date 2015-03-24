import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    expandable: doc.indexOf("\n") == -1 ? false : true

    height: content.height + 20

    Row {
        id: content

        spacing: 10

        height: expanded ? 40 + documentation.paintedHeight : 40

        anchors.verticalCenter: parent.verticalCenter

        Icon {
            name: expanded ? "chevron-up-white-16x16" : "chevron-down-white-16x16"
            opacity: expandable ? 1 : 0

            width: 10
            height: 10

            y: 2

            anchors.verticalCenter: parent.verticalCenter
        }

        Icon {
            id: icon

            name: "plugin2-white"
            width: 27
            height: 27

            y: 5
        }

        Column {
            spacing: 5

            Label {
                text: message
                style: "title"
            }

            TextArea {
                id: documentation

                property string docstring: doc ? doc : "No documentation"

                text: expanded ? docstring : docstring.split("\n")[0]
                opacity: 0.5
                maximumLineCount: expanded ? 99999 : 1

                width: root.width - icon.width
                elide: Text.ElideRight
            }
        }
    }
}