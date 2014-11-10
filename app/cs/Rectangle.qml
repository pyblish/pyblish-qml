import QtQuick 2.3

import "../js/modelService.js" as Model

/*
 * A generic rectangle
 * Consider it a baseclass for every rectangle used
*/
Rectangle {
    id: root
    property bool outwards: true

    // An outwards rectangle is naturally lighter, whereas
    // an inwards rectangle is darker. This can be overridden.
    color: Qt.darker(Model.color.background, outwards ? 0.9:1.2)

    /*
     * Outer border
    */
    Rectangle {
        color: "transparent"
        anchors.fill: parent
        anchors.margins: root.outwards ? 0:1
        border {
             width: 1
             color: Qt.darker(Model.color.background, 2)
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
             color: Qt.lighter(Model.color.background, 1.2)
        }
    }
}