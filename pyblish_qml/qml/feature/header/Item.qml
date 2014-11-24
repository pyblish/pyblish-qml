import QtQuick 2.3

import "../generic" as Generic
import "../service/model.js" as Model
import "headerController.js" as Ctrl

/*
 * Header
 *
 * Description
 *      Main header, used for moving the application
 *      along with closing, minimizing and logo display.
*/
Generic.Rectangle {
    property alias pyblishVersion: debugVersion.text
    property alias host: debugHost.text
    property bool logoContainsMouse
    
    signal logoPressed

    width: 200
    height: Model.size.headerHeight


    /*
     * Logo mouse area
     *
     * Description
     *      Triggered when entering the area
     *      occupied by the logotype in the upper-left corner.
    */
    MouseArea {
        anchors.fill: parent
        anchors.rightMargin: parent.width - headerImage.width
        hoverEnabled: true

        onEntered: logoContainsMouse = true;
        onExited: logoContainsMouse = false;
    }

    /*
     * Main mouse area
     *
     * Description
     *      Used for moving the window.
    */
    MouseArea {
        property real lastMouseX: 0
        property real lastMouseY: 0

        anchors.fill: parent
        anchors.leftMargin: headerImage.width

        acceptedButtons: Qt.LeftButton

        onPressed: {
            lastMouseX = mouseX
            lastMouseY = mouseY
        }

        onPositionChanged: {
            root.x += mouseX - lastMouseX
            root.y += mouseY - lastMouseY
        }
    }

    /*
     * Logo button
     *
     *
    */
    Image {
        id: headerImage
        source: Model.image.logo
        anchors.verticalCenter: parent.verticalCenter
        x: 4
        opacity: logoContainsMouse ? 1.0 : 0.7

        Behavior on opacity {
            NumberAnimation {
                duration: 200
                easing.type: Easing.OutQuint
            }
        }
    }

    /*
     * Debug info
     *
     * This item is shown upon hovering the main logo
    */
    Row {
        id: debugInfo

        property int margin: 10

        anchors.fill: parent
        anchors.leftMargin: headerImage.width + debugInfo.margin
        anchors.rightMargin: headerButtons.width
        opacity: logoContainsMouse ? 1.0 : 0.0

        Behavior on opacity {
            NumberAnimation {
                duration: 50
                easing.type: Easing.OutQuint
            }
        }

        Item {
            width: debugVersion.paintedWidth + debugInfo.margin
            height: parent.height
            anchors.verticalCenter: parent.verticalCenter

            Generic.Text {
                id: debugVersion
                anchors.centerIn: parent
                text: "0.0.0"
            }
        }

        Item {
            width: debugIcon.width + debugInfo.margin
            height: parent.height
            anchors.verticalCenter: parent.verticalCenter

            Image {
                id: debugIcon
                anchors.centerIn: parent
                source: Model.image.communication
            }
        }


        Item {
            width: debugHost.paintedWidth + debugInfo.margin
            height: parent.height
            anchors.verticalCenter: parent.verticalCenter

            Generic.Text {
                id: debugHost
                anchors.centerIn: parent
                text: "Python"
            }
        }
    }

    /*
     * Header buttons
     *
     *
    */
    Row {
        id: headerButtons

        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: Model.margins.main
        }

        spacing: Model.margins.alt

        Generic.Button {
            id: closeButton
            source: Model.image.close
            width: 30
            height: 30

            onClicked: Ctrl.closeClickedHandler();
        }
    }
}