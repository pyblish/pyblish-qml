import QtQuick 2.3
import Pyblish 0.1


Item {
    id: view

    property int elevation

    property color color: Theme.backgroundColor

    property int margins: 5

    Item {
        id: fill

        anchors.fill: parent

        visible: view.elevation != 0

        Rectangle {
            id: outerBorder

            color: Qt.darker(view.color, view.elevation > 0 ? 0.9 : 1.2)

            anchors {
                fill: parent
                margins: view.elevation > 0 ? 0 : 1
            }

            border {
                 width: 1
                 color: Qt.darker(view.color, 2)
            }
        }

        Rectangle {
            id: innerBorder

            color: "transparent"

            anchors {
                fill: parent
                margins: view.elevation > 0 ? 1 : 0
            }

            border {
                 width: 1
                 color: Qt.lighter(view.color, 1.2)
            }
        }
    }
}