import QtQuick 2.3
import Pyblish 0.1


View {
    id: actionBar

    height: 45

    elevation: 1

    property list<Action> actions

    Row {
        anchors.fill: parent

        Repeater {
            id: repeater
            model: actionBar.actions
            delegate: IconButton {
                id: iconAction

                action: actionBar.actions[index]

                // size: name == "content/add" ? units.dp(30) : units.dp(27)
                anchors.verticalCenter: parent ? parent.verticalCenter : undefined
            }
        }
    }

    Component {
        id: tab

        View {
            width: 40 + row.width
            height: actionBar.height

            elevation: 1

            Ink {
                anchors.fill: parent

                onClicked: modelData.action
            }

            Row {
                id: row

                anchors.centerIn: parent

                spacing: 10

                Icon {
                    anchors.verticalCenter: parent.verticalCenter
                    name: modelData.hasOwnProperty("icon") ? modelData.icon : ""
                    visible: name != ""
                }

                Label {
                    id: label
                    text: modelData.hasOwnProperty("text") ? modelData.text : modelData
                    anchors.verticalCenter: parent.verticalCenter
                }
            }
        }
    }
}