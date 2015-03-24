import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {

    height: 27

    Row {
        spacing: 10

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
            name: "instance-white"
            width: 27
            height: 27
        }

        Label {
            text: message
            style: "subheading"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}