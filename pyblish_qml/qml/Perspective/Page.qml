import QtQuick 2.3
import QtQuick.Layouts 1.0
import Pyblish 0.1
import "../Delegates.js" as Delegates


Item {
    id: root

    property QtObject item

    Column {
        anchors.fill: parent
        spacing: -1

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
            elevation: 1
            width: parent.width
            height: root.height - actionBar.height

            View {
                anchors.fill: parent
                anchors.margins: 5

                elevation: -1

                ListView {
                    id: body

                    anchors {
                        top: header.bottom
                        bottom: parent.bottom
                        left: parent.left

                        leftMargin: 7
                        rightMargin: 7
                        bottomMargin: 2
                    }

                    clip: true

                    width: scrollbar.visible ? parent.width - 40 : parent.width - anchors.leftMargin * 2

                    boundsBehavior: Flickable.StopAtBounds

                    spacing: -1

                    model: [
                        {type: "spacer"},
                        {
                            type: "documentation",
                            name: "Documentation",
                            closed: true,
                            item: root.item
                        },
                        {
                            type: "errors",
                            name: "Errors",
                            closed: false,
                            model: app.errorProxy
                        },
                        {
                            type: "records",
                            name: "Records",
                            closed: false,
                            model: app.recordProxy
                        },
                        // {
                        //     "type": "plugins",
                        //     "name": "Plug-ins",
                        //     "tab": true,
                        //     "closed": false,
                        //     "model": app.pluginProxy
                        // },
                        // {
                        //     "type": "instances",
                        //     "name": "Instances",
                        //     "tab": true,
                        //     "closed": false,
                        //     "model": app.instanceProxy
                        // },
                        {type: "spacer"},
                    ]

                    delegate: Loader {
                        width: ListView.view.width
                        sourceComponent: Delegates.components[modelData.type]
                    }
                }

                Header {
                    id: header

                    anchors {
                        top: parent.top
                        left: parent.left
                        right: parent.right

                        leftMargin: 10
                        rightMargin: 10
                    }

                    Title {
                        name: item.name
                        width: parent.width
                    }

                    Gadget {
                        name: item.name
                        width: parent.width
                    }

                    Spacer {
                        height: 10
                    }
                }

                Scrollbar {
                    id: scrollbar

                    anchors.top: body.top
                    anchors.bottom: body.bottom
                    anchors.right: parent.right
                    anchors.margins: 2

                    width: 20

                    flickable: body
                }

                Rectangle {
                    id: shadow
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.top: header.bottom
                    anchors.leftMargin: 2
                    anchors.rightMargin: 2

                    height: 10

                    gradient: Gradient {
                        GradientStop { position: 0.0; color: Theme.alpha("black", 0.3) }
                        GradientStop { position: 1.0; color: "transparent" }
                    }
                }
            }
        }
    }
}