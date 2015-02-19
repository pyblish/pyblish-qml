import QtQuick 2.3


View {
    id: tabbar

    height: 45

    clip: true

    property var tabs: []
    property int currentIndex: 0

    Row {

        anchors.fill: parent

        spacing: -2

        Repeater {
            id: repeater
            model: tabbar.tabs

            delegate: View {
                id: tabItem

                property int heightOffset: 8

                width: 40 + row.width
                height: tabbar.height - (selected() ? 2 : heightOffset)

                function selected() {
                    return index == tabbar.currentIndex
                }

                z: selected() ? 1 : 0
                y: selected() ? 2 : heightOffset

                Behavior on y {
                    NumberAnimation {
                        duration: 50
                    }
                }

                Behavior on height {
                    NumberAnimation {
                        duration: 50
                    }
                }

                Ink {
                    anchors.fill: parent

                    onClicked: {
                        tabbar.currentIndex = index
                    }
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
}