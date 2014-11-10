import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/modelService.js" as Model
import "js/restService.js" as Rest
import "js/appController.js" as AppCtrl


Cs.Window {
    id: root
    width: 400
    height: 500
    minimumWidth: 200
    minimumHeight: 200

    /*
     * Quit Animation
     * This sequence is activated when the
     * user hits the close button.
    */
    SequentialAnimation {
        id: quitAnimation
        running: false

        NumberAnimation {
            target: root
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
    SequentialAnimation {
        id: startAnimation
        running: false

        NumberAnimation {
            target: root
            property: "height"
            from: 0
            to: root.height
        }
    }

    Cs.Header {
        id: header
        z: 1  // Keep above all other items

        /*
         * Main header, used for moving the application
         * along with closing, minimizing and logo display.
        */
        Image {
            id: headerImage
            source: "img/logo-white.png"
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
                    quitAnimation.stopped.connect(Qt.quit);
                    quitAnimation.start();
                }
            }
        }
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

        Component {
            id: itemDelegateComponent
            Cs.ItemDelegate {
                width: ListView.view.width
            }
        }

        ListView {
            id: canvasList
            anchors.fill: parent
            anchors.margins: 3

            model: ListModel {
                id: canvasModel
            }
            spacing: 1
            delegate: itemDelegateComponent
        }
    }

    Item {
        id: footer
        anchors {
            left: parent.left
            right: parent.right
            bottom: parent.bottom
        }

        height: Model.size.footerHeight

        Cs.Button {
            id: publishButton
            width: 30
            height: 30
            anchors {
                right: parent.right
                margins: Model.margins.main
            }
        }
    }

    Component.onCompleted: {
        AppCtrl.init();
    }
}
