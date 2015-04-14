import QtQuick 2.3
import Pyblish 0.1


Item {
    height: 100
    
    View {
        radius: 5

        color: Qt.darker(Theme.backgroundColor, 1.5)

        anchors.fill: parent
        anchors.margins: 10

        Label {
            id: title
            style: "title"
            text: object.name

            anchors.verticalCenter: parent.verticalCenter
            anchors.fill: parent
            anchors.leftMargin: 10
        }
    }
}