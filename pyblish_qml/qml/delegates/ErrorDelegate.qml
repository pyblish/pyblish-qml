import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    expandable: true

    height: content.height + 10

    Row {
        id: content

        spacing: 10

        width: parent.width

        anchors.verticalCenter: parent.verticalCenter

        clip: true

        Icon {
            id: toggle

            name: expanded ? "chevron-up-white-16x16" : "chevron-down-white-16x16"
            opacity: expandable ? 1 : 0

            width: 10
            height: 10

            y: 2

            anchors.verticalCenter: parent.verticalCenter
        }

        Icon {
            id: icon

            name: "error-red-32x32"

            width: 27
            height: 27
        }

        Column {
            id: body

            spacing: 10

            width: root.width - icon.width - toggle.width - content.spacing

            property bool hasLongMessage: message.indexOf("\n") != -1 ? true : false
            property string shortMessage: message.split("\n")[0]
            property string longMessage: message

            y: 5  // Center text to icon
            height: implicitHeight + 5

            Label {
                text: root.expanded ? body.longMessage : body.shortMessage
                maximumLineCount: root.expanded ? 99999 : 1

                color: Qt.lighter("red", 1.5)

                elide: Text.ElideRight
                wrapMode: root.expanded ? Text.WordWrap : Text.NoWrap

                width: parent.width
            }

            Column {
                visible: root.expanded

                Repeater {

                    model: [
                        {
                            "key": "Filename",
                            "value": fname
                        },
                        {
                            "key": "Line Number",
                            "value": line_number
                        },
                        {
                            "key": "Function",
                            "value": func
                        },
                        {
                            "key": "Exception",
                            "value": exc
                        }
                    ]

                    Row {
                        spacing: 5
                        opacity: 0.5

                        Label {
                            text: modelData.key
                            backgroundColor: Theme.alpha("white", 0.1)
                        }

                        Label {
                            text: modelData.value
                        }
                    }
                }
            }
        }
    }
}