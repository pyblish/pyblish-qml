import QtQuick 2.0
import "."
import ".."


Ink {
    id: listItem

    z: -1

    property int elevation: 0
    property int margins: 16

    property bool selected
    property bool interactive: true

    property color backgroundColor: elevation > 0 ? "white" : "transparent"
    property color tintColor: selected ? Qt.rgba(0,0,0,0.07) : listItem.containsMouse ? Qt.rgba(0,0,0,0.03) : Qt.rgba(0,0,0,0)

    enabled: listItem.interactive

    Rectangle {
        id: tint
        anchors.fill: parent
        color: Qt.tint(backgroundColor, tintColor)
        antialiasing: parent.rotation || radius > 0 ? true : false
        clip: true

        Behavior on color {
            ColorAnimation { duration: 200 }
        }
    }
}