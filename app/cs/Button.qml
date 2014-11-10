import QtQuick 2.3

import "../js/modelService.js" as Model
import "../cs" as Cs


Cs.Rectangle {
    id: root
    signal clicked

    property string source: ""
    
    clip: true

    MouseArea {
        anchors.fill: parent
        hoverEnabled: true

        onClicked: {
            root.clicked();
            anim.restart();
            clicked.x = mouse.x - clicked.width / 2 
            clicked.y = mouse.y - clicked.height / 2
        }
        onEntered: hover.opacity = 1
        onExited: hover.opacity = 0
    }

    Rectangle {
        id: hover
        anchors.fill: parent
        anchors.margins: 1
        color: Qt.lighter(Model.color.background, 1.6)
        opacity: 0

        Behavior on opacity {
            NumberAnimation {
                duration: 100
                easing.type: Easing.OutQuad
            }
        }
    }

    Item {
        id: clicked
        width: parent.width * 2
        height: parent.height * 2

        Rectangle {
            id: clickedRectangle
            anchors.fill: parent
            anchors.margins: root.width / 2
            radius: 100
            color: "white"
            opacity: 0

            ParallelAnimation {
                id: anim
                running: false

                NumberAnimation {
                    target: clickedRectangle
                    property: "anchors.margins"
                    from: root.width
                    to: 2
                    duration: 400
                    easing.type: Easing.OutQuint
                }
                NumberAnimation {
                    target: clickedRectangle
                    property: "opacity"
                    duration: 1000
                    from: 1
                    to: 0
                    easing.type: Easing.OutQuint
                }
            }
        }
    }

    Image {
        source: root.source
        fillMode: Image.PreserveAspectCrop
        anchors.centerIn: parent
    }
}