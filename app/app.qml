import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/modelService.js" as Model
import "js/restService.js" as Rest
import "js/appController.js" as AppCtrl


Window {
    id: root
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

            // MouseArea {
            //     anchors.fill: parent


            // }

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

            Component {
                id: sectionDelegateComponent
                Cs.SectionDelegate {
                    width: ListView.view.width
                }
            }

            Component {
                id: highlightComponentDelegate
                Cs.HighlightComponent {
                    // width: ListView.view.width
                }
            }

            ListView {
                id: canvasList
                focus: true
                anchors.fill: parent
                anchors.margins: 3

                model: ListModel { id: canvasModel }
                section.property: "family"
                section.delegate: sectionDelegateComponent
                spacing: 1
                delegate: itemDelegateComponent
                highlight: highlightComponentDelegate
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

                onClicked: AppCtrl.publish()
            }
        }
    }

    Component.onCompleted: {
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;
        startAnimation.start();
        AppCtrl.init();
    }
}
