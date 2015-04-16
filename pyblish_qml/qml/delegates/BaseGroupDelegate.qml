import QtQuick 2.3
import QtQuick.Layouts 1.1
import Pyblish 0.1


Column {
    id: root

    property Component item
    property alias gutter: gutter.visible

    property bool opened: true

    spacing: 0

    MouseArea {
        id: header

        height: 25

        width: parent.width

        onClicked: opened = !opened

        View {
            anchors.fill: parent
            elevation: 1
        }

        Row {
            anchors.fill: parent
            anchors.leftMargin: 10
            spacing: 10

            AwesomeIcon {
                name: "caret-right"
                rotation: opened ? 90 : 0

                anchors.verticalCenter: parent.verticalCenter

                size: 16
            }

            Label {
                text: modelData.name
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    Rectangle {
        id: body

        width: parent.width

        height: opened ? loader.item.height : 0
        visible: opened

        color: Qt.darker(Theme.backgroundColor, 2)

        Rectangle {
            id: gutter

            visible: false

            color: Qt.darker(Theme.backgroundColor, 3)

            width: icon.width

            anchors.top: parent.top
            anchors.bottom: parent.bottom

            Icon {
                id: icon
                name: "button-expand"
                visible: false
            }
        }

        Loader {
            id: loader

            visible: opened
            width: parent.width

            sourceComponent: opened ? root.item : null
        }
    }
}