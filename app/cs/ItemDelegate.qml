import QtQuick 2.3

import "../cs" as Cs
import "../js/listController.js" as Ctrl


Item {
    height: 20
    width: parent.width

    Item {
        anchors.top: parent.top
        anchors.bottom: parent.bottom

        Rectangle {
            id: indicatorContainer
            color: "transparent"
            width: 10
            anchors {
                top: parent.top
                bottom: parent.bottom
            }

            Rectangle {
                id: indicator
                visible: selected ? true : false

                anchors {
                    top: parent.top
                    bottom: parent.bottom
                    left: parent.left
                }

                width: 1
                color: "yellow"
            }

            MouseArea {
                anchors.fill: parent
                hoverEnabled: true
                onClicked: Ctrl.itemIndicatorClickedHandler(index)
                onEntered: indicatorContainer.color = "red"
                onExited: indicatorContainer.color = "transparent"
            }
        }

        Cs.Text {
            id: text
            text: instance
            anchors.left: indicatorContainer.right
            anchors.leftMargin: 5
            anchors.verticalCenter: parent.verticalCenter

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent

                onClicked: Ctrl.itemClickedHandler(index)
                onEntered: hover.opacity = 0.05
                onExited: hover.opacity = 0
            }
        }
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