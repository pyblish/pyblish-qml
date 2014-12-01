import QtQuick 2.3

import "../service/constant.js" as Constant

/*
 * A generic rectangle
 * Consider it a baseclass for every rectangle used
*/
Rectangle {
    id: root
    property bool outwards: true

    implicitWidth: 100
    implicitHeight: 100

    // An outwards rectangle is naturally lighter, whereas
    // an inwards rectangle is darker. This can be overridden.
    color: Qt.darker(Constant.color.background, outwards ? 0.9 : 1.2)

    /*
     * Outer border
    */
    Rectangle {
        color: "transparent"
        anchors.fill: parent
        anchors.margins: root.outwards ? 0:1
        border {
             width: 1
             color: Qt.darker(Constant.color.background, 2)
        }
    }

    /*
     * Inner border
    */
    Rectangle {
        color: "transparent"
        anchors.fill: parent
        anchors.margins: root.outwards ? 1:0
        border {
             width: 1
             color: Qt.lighter(Constant.color.background, 1.2)
        }
    }
}