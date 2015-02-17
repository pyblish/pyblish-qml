import QtQuick 2.3
import "."
import ".."


BaseListItem {
    id: listItem

    property bool active: false
    property bool checked: false
    property alias status: indicator.status

    property alias text: label.text

    Row {
        spacing: 5
        anchors.fill: parent
        anchors.leftMargin: 5
        anchors.rightMargin: 5

        CheckBox {
            id: indicator
            active: listItem.active
            checked: listItem.checked
            anchors.verticalCenter: parent.verticalCenter

            onClicked: {
                listItem.clicked(mouse)
            }
        }

        Label {
            id: label
            opacity: active ? 1.0 : 0.5
            anchors.verticalCenter: parent.verticalCenter

            Behavior on color {
                ColorAnimation {
                    duration: 100
                }
            }
        }
    }
}
