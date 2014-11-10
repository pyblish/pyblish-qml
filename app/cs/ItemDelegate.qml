import QtQuick 2.3

import "../js/appController.js" as AppCtrl


Item {
    height: 20

    Item {
        anchors.fill: parent
        anchors.leftMargin: 20

        Text {
            id: text
            text: instance
            color: "white"
            renderType: Text.QtRendering
            font.family: mainFont.name
            anchors.verticalCenter: parent.verticalCenter
        }

    }

    MouseArea {
        hoverEnabled: true
        anchors.fill: parent

        onClicked: AppCtrl.itemClickedHandler(index)
        onEntered: hover.opacity = 0.05
        onExited: hover.opacity = 0
    }

    Rectangle {
        id: hover
        anchors.fill: parent
        color: "white"
        opacity: 0

        Behavior on opacity {
            NumberAnimation {
                duration: 200
                easing.type: Easing.OutCubic
            }
        }
    }
}