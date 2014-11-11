import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/appController.js" as Ctrl
import "js/modelService.js" as Model

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
    property alias startAnimation: startAnimation
    property alias quitAnimation: quitAnimation
    property alias message: message
    property bool _closeOk: false

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

        Cs.Rectangle {
            id: list
            outwards: false
            clip: true

            anchors {
                top: header.bottom
                bottom: footer.top
                left: parent.left
                right: parent.right

                margins: Model.margins.main
            }

            ListView {
                id: listList
                focus: true
                anchors.fill: parent
                anchors.margins: Model.margins.main
                spacing: 1

                model: ListModel { id: listModel }

                delegate: Cs.ItemDelegate {}
                highlight: Cs.HighlightComponent {}
                section.property: "family"
                section.delegate: Cs.SectionDelegate {}
            }
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

    // Todo: This is duplicated in closeClickedHandler
    onClosing: {
        Ctrl.quit(close);
        // startAnimation.stop();
        // close.accepted = root._closeOk

        // quitAnimation.stopped.connect(function () {
        //     root._closeOk = true;
        //     Qt.quit();
        // });

        // if (!root._closeOk) {
        //     quitAnimation.start()
        // };

        // console.log("Closing");
    }
}
