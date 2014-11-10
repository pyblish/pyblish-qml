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

    /*
     * Main header, used for moving the application
     * along with closing, minimizing and logo display.
    */
    Image {
        id: headerImage
        source: "../img/logo-white.png"
        anchors.verticalCenter: parent.verticalCenter
        x: 4
    }

    Row {
        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: Model.margins.main
        }

        spacing: Model.margins.alt

        Cs.Button {
            id: closeButton
            source: "../img/button-close.png"
            width: 30
            height: 30

            onClicked: {
                root.minimumHeight = header.height
                startAnimation.stop();
                quitAnimation.stopped.connect(Qt.quit);
                quitAnimation.start();
            }
        }
    }
}