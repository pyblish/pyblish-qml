import QtQuick 2.3

import "../cs" as Cs

Cs.Text {
    id: root
    opacity: 0
    anchors.verticalCenter: parent.verticalCenter

    property alias animation: messageAnimation

    SequentialAnimation {
        id: messageAnimation

        ParallelAnimation {
            NumberAnimation {
                target: root
                property: "x"
                from: 5
                to: 20
                duration: 1000
                easing.type: Easing.OutQuint
            }
            NumberAnimation {
                target: root
                property: "opacity"
                from: 0
                to: 1
                duration: 500
                easing.type: Easing.OutQuint
            }
        }

        PauseAnimation {
            duration: 1000
        }

        NumberAnimation {
            target: root
            property: "opacity"
            to: 0
            duration: 2000
        }
    }
}