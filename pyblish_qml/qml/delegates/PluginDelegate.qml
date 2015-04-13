import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    expandable: item.doc && item.doc.indexOf("\n") != -1 ? true : false

    height: bodyItem.height + 5

    body: Row {
        id: content

        spacing: 10

        height: expanded ? 40 + documentation.paintedHeight : 40

        anchors.verticalCenter: parent.verticalCenter

        AwesomeIcon {
            id: icon
            name: "plug"
            size: 16
        }

        Column {
            spacing: 5

            width: root.width - 
                   icon.width -
                   content.spacing -
                   root.toggle.width -
                   10

            Label {
                text: item.message
                // style: "title"
                width: parent.width
                elide: Text.ElideRight
            }

            TextArea {
                id: documentation

                property string docstring: item.doc ? item.doc : "No documentation"

                text: expanded ? docstring : docstring.split("\n")[0]
                opacity: 0.5
                maximumLineCount: expanded ? 99999 : 1

                width: parent.width
                elide: Text.ElideRight
            }
        }
    }
}