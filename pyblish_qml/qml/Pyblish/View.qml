import QtQuick 2.3
import Pyblish 0.1


Item {
    id: view

    /*!
       An outwards rectangle is naturally lighter, whereas
       an inwards rectangle is darker.
    */
    property var styles: ["inwards", "outwards"]
    property string style: "outwards"

    property color color: Theme.backgroundColor

    property int margins: 5

    Rectangle {
        id: outerBorder
        color: Qt.darker(view.color, style == "outwards" ? 0.9 : 1.2)

        anchors {
            fill: parent
            margins: view.style == "outwards" ? 0 : 1
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
            margins: view.style == "outwards" ? 1 : 0
        }

        border {
             width: 1
             color: Qt.lighter(view.color, 1.2)
        }
    }
}