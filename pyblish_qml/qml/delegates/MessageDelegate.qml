import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    height: bodyItem.__height

    body: Row {
        id: content

        property real __height: label.paintedHeight

        spacing: 10
        anchors.verticalCenter: parent.verticalCenter

        Icon {
            id: toggle
        
            name: "button-publish"
            opacity: expandable ? 1 : 0
            rotation: expanded ? 90 : 0

            anchors.verticalCenter: parent.verticalCenter

            y: 2
        }

        Label {
            id: label
            text: message

            elide: Text.ElideRight
            
            width: root.width - toggle.width - content.spacing
        }
    }
}