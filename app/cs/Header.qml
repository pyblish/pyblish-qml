import QtQuick 2.3

import "../js/modelService.js" as Model
import "../cs" as Cs

/*
 * Header
*/
Cs.Rectangle {
    height: Model.size.headerHeight
    anchors {
        left: parent.left
        right: parent.right
    }

    MouseArea {
        anchors.fill: parent

        property real lastMouseX: 0
        property real lastMouseY: 0

        acceptedButtons: Qt.LeftButton
        onPressed: {
            if (mouse.button == Qt.LeftButton) {
                lastMouseX = mouseX
                lastMouseY = mouseY
            }
        }
        onMouseXChanged: root.x += (mouseX - lastMouseX)
        onMouseYChanged: root.y += (mouseY - lastMouseY)
    }
}