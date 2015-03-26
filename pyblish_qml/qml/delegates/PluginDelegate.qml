import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    expandable: doc && doc.indexOf("\n") != -1 ? true : false

    height: bodyItem.height + 5

    body: Row {
        id: content

        spacing: 10

        height: expanded ? 40 + documentation.paintedHeight : 40

        anchors.verticalCenter: parent.verticalCenter

        Icon {
            id: icon
            name: "plugin2-white-27x27"
        }

        Column {
            spacing: 5

            width: root.width - icon.width - content.spacing

            Label {
                text: message
                // style: "title"
                width: parent.width
                elide: Text.ElideRight
            }

            TextArea {
                id: documentation

                property string docstring: doc ? doc : "No documentation"

                text: expanded ? docstring : docstring.split("\n")[0]
                opacity: 0.5
                maximumLineCount: expanded ? 99999 : 1

                width: parent.width
                elide: Text.ElideRight
            }
        }
    }
}