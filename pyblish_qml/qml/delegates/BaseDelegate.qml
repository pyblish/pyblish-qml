import QtQuick 2.3
import Pyblish 0.1


MouseArea {
    id: root

    clip: true
    hoverEnabled: true

    property color color: "white"

    property bool expandable
    property bool expanded

    onClicked: {
        if (expandable)
            expanded = !expanded
    }
}