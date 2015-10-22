import QtQuick 2.3
import QtQuick.Layouts 1.1

import Pyblish 0.1
import Pyblish.ListItems 0.1


MouseArea {
    id: root

    property bool active: true
    property bool available: true
    property bool checked: false
    property string icon: ""

    property alias text: label.text
    property int margins: 5

    RowLayout {
        id: body

        anchors.fill: parent

        AwesomeIcon {
            Layout.fillHeight: true
            width: 30
            name: icon
            opacity: 0.5
        }

        Label {
            id: label
            opacity: (active && available) ? 1.0 : 0.5

            Layout.fillWidth: true
            anchors.verticalCenter: parent.verticalCenter
            font.strikeout: !available
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