import QtQuick 2.3
import QtQuick.Layouts 1.1

import Pyblish 0.1
import Pyblish.ListItems 0.1


MouseArea {
    id: listItem

    hoverEnabled: true

    property bool active: false
    property bool checked: false

    property alias text: label.text
    property int margins: 5

    RowLayout {
        id: body

        spacing: 0
        anchors.fill: parent

        Item {
            id: icon
            Layout.fillHeight: true
            width: 30
        }

        Label {
            id: label
            opacity: active ? 1.0 : 0.5

            Layout.fillWidth: true
            anchors.verticalCenter: parent.verticalCenter
        }
    }

    Rectangle {
        color: "white"
        opacity: 0.1
        visible: containsMouse

        anchors.fill: parent
        anchors.margins: 1
    }
}
