import QtQuick 2.3


Item {
    height: 20

    Item {
        anchors.fill: parent
        anchors.margins: 5

        Text {
            id: text
            text: instance
            color: "white"
            font.family: "Courier New"
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}