import QtQuick 2.3
import Pyblish 0.1

Ink {
    id: button

    property string text: ""
    property string icon: ""
    
    width: 30
    height: 30

    View {
        anchors.fill: parent

        Row {
            id: row

            anchors.centerIn: parent
            spacing: 10

            Icon {
                anchors.verticalCenter: parent.verticalCenter
                name: button.icon
                visible: button.icon != ""
            }

            Label {
                id: label
                text: button.text
                style: "button"
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}