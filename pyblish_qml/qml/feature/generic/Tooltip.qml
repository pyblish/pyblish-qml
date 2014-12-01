import QtQuick 2.3

import "." as Generic


/*
 * Tooltip implementation
 *
*/
Item {
    id: root
    property string text
    property int margin: 10
    property bool visible

    visible: text  // Display if there's text
    anchors.fill: parent

    Rectangle {
        id: _container
        color: "black"
        width: _text.paintedWidth + margin
        height: _text.paintedHeight + margin
        radius: 5
        visible: false

        Generic.Text {
            id: _text
            text: root.text
            anchors.centerIn: parent
        }
    }
}