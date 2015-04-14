import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    height: {
        if (loader.status == Loader.Ready)
            return loader.item.height + 5
        return 0
    }

    body: Row {
        id: content

        spacing: 10
        anchors.verticalCenter: parent.verticalCenter

        AwesomeIcon {
            id: toggle

            size: 16
            width: 16

            name: "info"
        }

        Label {
            id: label
            text: object.message

            elide: Text.ElideRight
            
            width: content.width - toggle.width - content.spacing
        }
    }
}