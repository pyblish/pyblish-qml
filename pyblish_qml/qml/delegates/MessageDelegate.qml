import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    height: label.paintedHeight

    Row {
        id: content

        spacing: 10
        anchors.verticalCenter: parent.verticalCenter

        Icon {
            id: toggle
        
            name: expanded ? "chevron-up-white-16x16" : "chevron-down-white-16x16"
            opacity: expandable ? 1 : 0

            width: 10
            height: 10

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