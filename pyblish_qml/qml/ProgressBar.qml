import QtQuick 2.3
import "."


Item {
    id: progressBar

    property real progress: 0
    property color color: Constant.itemColor

    clip: true

    Rectangle {
        id: bar

        x: -width * (1 - progressBar.progress)
        height: parent.height
        width: parent.width

        color: progressBar.color

        Behavior on x {
            NumberAnimation {
                duration: 100
            }
        }
    }
}