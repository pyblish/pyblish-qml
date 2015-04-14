import QtQuick 2.3
import Pyblish 0.1
import "Delegates.js" as Delegates


Rectangle {
    id: root

    color: Theme.backgroundColor

    Column {
        anchors.fill: parent

        ActionBar {
            id: actionBar

            width: parent.width
            height: 50

            actions: [
                Action {
                    iconName: "button-back"
                    onTriggered: stack.pop()
                }
            ]

            elevation: 1
        }

        View {
            elevation: -1
            width: parent.width
            height: root.height - actionBar.height

            ListView {

                anchors.fill: parent
                anchors.margins: 5

                boundsBehavior: Flickable.StopAtBounds

                spacing: -1

                model: [
                    {
                        "type": "gadget",
                        "name": "Gadget",
                        "tab": false,
                        "model": app.gadgetProxy
                    },
                    {
                        "name": "Records",
                        "tab": true,
                        "model": app.recordProxy
                    },
                    {
                        "name": "Errors",
                        "tab": true,
                        "model": app.errorProxy
                    }
                ]

                delegate: Column {
                    width: ListView.view.width

                    View {
                        color: "gray"
                        height: text.paintedHeight + 10
                        width: parent.width
                        elevation: 1
                        z: 2

                        visible: modelData.tab

                        Row {
                            anchors.fill: parent
                            anchors.leftMargin: 10
                            spacing: 10

                            AwesomeIcon {
                                name: "caret-right"
                                size: 16
                                anchors.verticalCenter: parent.verticalCenter
                                rotation: 90
                            }

                            Label {
                                id: text
                                text: modelData.name
                                anchors.verticalCenter: parent.verticalCenter
                            }
                        }
                    }

                    View {
                        width: parent.width
                        height: Math.min(listView.contentHeight, 180)

                        ListView {
                            id: listView

                            anchors.fill: parent

                            model: modelData.model

                            clip: true
                            boundsBehavior: Flickable.StopAtBounds

                            delegate: Loader {
                                width: ListView.view.width
                                sourceComponent: Delegates.components[modelData.type || object.type]
                            }
                        }
                    }
                }
            }
        }
    }
}