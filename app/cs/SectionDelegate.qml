import QtQuick 2.3

import "../js/modelService.js" as Model


Item {
    height: 20
    // color: Qt.darker(Model.color.background, 1.5)

    Item {
        anchors.fill: parent
        anchors.margins: 5

        Text {
            id: text
            renderType: Text.QtRendering
            text: section
            color: "white"
            opacity: 0.5
            font.family: mainFont.name
            anchors.verticalCenter: parent.verticalCenter
        }
    }
}