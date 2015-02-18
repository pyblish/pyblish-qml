import QtQuick 2.3
import "."


/*
 * A generic rectangle
 * Consider it a baseclass for every rectangle used
*/
Rectangle {
    id: root
    
    property var styles: ["inwards", "outwards"]
    property string style: "outwards"

    // An outwards rectangle is naturally lighter, whereas
    // an inwards rectangle is darker. This can be overridden.
    color: Qt.darker(Constant.backgroundColor, style == "outwards" ? 0.9 : 1.2)

    /*
     * Outer border
    */
    Rectangle {
        color: "transparent"
        anchors.fill: parent
        anchors.margins: root.style == "outwards" ? 0 : 1

        border {
             width: 1
             color: Qt.darker(Constant.backgroundColor, 2)
        }
    }

    /*
     * Inner border
    */
    Rectangle {
        color: "transparent"
        anchors.fill: parent
        anchors.margins: root.style == "outwards" ? 1 : 0

        border {
             width: 1
             color: Qt.lighter(Constant.backgroundColor, 1.2)
        }
    }
}