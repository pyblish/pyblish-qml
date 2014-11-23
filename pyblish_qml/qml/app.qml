import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/modelService.js" as Model
import "js/appController.js" as Ctrl
import "js/hostService.js" as Host

/*
 * Main window
 *
 * Properties:
 *      header (alias): Main header
 *      startAnimation (alias): Initial animation
 *      endAnimation (alias): Animation upon quitting
 *      message (alias): Message at the lower left
 *      _closeOk (bool): Used internally
 *
*/
Window {
    property alias header: header
    property alias message: message
    property alias quitAnimation: quitAnimation
    property alias startAnimation: startAnimation

    id: root

    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"

    width: Model.size.windowWidth
    height: Model.size.windowHeight
    minimumWidth: Model.size.windowMinimumWidth
    minimumHeight: Model.size.windowMinimumHeight

    FontLoader {
        id: mainFont
        source: "font/OpenSans-Semibold.ttf"
    }

    Cs.QuitAnimation {
        id: quitAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }

    Cs.StartAnimation {
        id: startAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }

    Cs.Rectangle {
        id: container
        width: parent.width
        color: Model.color.background
        height: 0  // Modified with animation

        Cs.Header {
            id: header
            z: 1  // Keep above all other items
        }

        Cs.Text {
            id: connectionText
            text: "No connection"
            anchors.centerIn: parent
        }

        ListModel { id: instancesModel }

        Cs.InstancesItem {
            id: instancesItem
            model: instancesModel
            anchors.top: header.bottom
            anchors.bottom: footer.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Model.margins.main
            visible: false
        }

        Item {
            id: footer

            anchors {
                left: parent.left
                right: parent.right
                bottom: parent.bottom
                margins: Model.margins.main
            }

            height: Model.size.footerHeight

            Cs.Message {
                id: message
            }

            Cs.Button {
                id: publishButton
                width: parent.height
                height: parent.height
                anchors.right: parent.right
                anchors.verticalCenter: parent.verticalCenter

                source: "../img/button-expand.png"
                onClicked: Ctrl.publish()
            }
        }
    }

    Component.onCompleted: {
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;

        startAnimation.start();
        Ctrl.init();

    }

    onClosing: Ctrl.quit(close);
}
