import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/appController.js" as Ctrl
import "js/modelService.js" as Model


Window {
    id: root

    property alias header: header
    property alias startAnimation: startAnimation
    property alias quitAnimation: quitAnimation
    property alias message: message
    property bool closeOk: false

    flags: Qt.FramelessWindowHint
    color: "transparent"

    width: Model.size.windowWidth
    height: Model.size.windowHeight
    minimumWidth: Model.size.windowMinimumWidth
    minimumHeight: Model.size.windowMinimumHeight

    FontLoader {
        id: mainFont
        source: "font/OpenSans-Semibold.ttf"
    }

    /*
     * Quit Animation
     * This sequence is activated when the
     * user hits the close button.
    */
    SequentialAnimation {
        id: quitAnimation
        running: false

        NumberAnimation {
            target: container
            property: "height"
            to: header.height
            duration: 400
            easing.type: Easing.OutCubic
        }

        PauseAnimation {
            duration: 50
        }

        NumberAnimation {
            target: root
            property: "opacity"
            to: 0
            duration: 200
        }
    }

    /*
     * Start Animation
     *
    */
    ParallelAnimation {
        id: startAnimation
        running: false

        NumberAnimation {
            target: container
            property: "opacity"
            from: 0
            to: 1
            duration: 500
            easing.type: Easing.OutQuint
        }

        NumberAnimation {
            target: container
            property: "height"
            from: root.height / 2
            to: root.height
            duration: 1000
            easing.type: Easing.OutQuint
        }
    }


    Cs.Rectangle {
        id: container
        width: parent.width
        height: 0
        color: Model.color.background

        Cs.Header {
            id: header
            z: 1  // Keep above all other items
        }

        Cs.Rectangle {
            id: canvas
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
                id: canvasList
                focus: true
                anchors.fill: parent
                anchors.margins: Model.margins.main
                spacing: 1

                model: ListModel { id: canvasModel }

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
        startAnimation.stop();
        close.accepted = root.closeOk

        quitAnimation.stopped.connect(function () {
            root.closeOk = true;
            Qt.quit();
        });

        if (!root.closeOk) {
            quitAnimation.start()
        };

        console.log("Closing");
    }
}
