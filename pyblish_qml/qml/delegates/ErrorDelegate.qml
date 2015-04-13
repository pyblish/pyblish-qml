import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    id: root

    expandable: true

    height: bodyItem.height + 5

    body: Row {
        id: content

        spacing: 10

        width: parent.width

        Icon {
            id: icon
            name: "error-red-16x16"
            anchors.verticalCenter: parent.verticalCenter
        }

        Column {
            id: body

            spacing: 10

            width: root.width -
                   icon.width -
                   content.spacing -
                   root.toggle.width -
                   10

            property bool hasLongMessage: item.message.indexOf("\n") != -1 ? true : false
            property string shortMessage: item.message.split("\n")[0]
            property string longMessage: item.message

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
                            "value": item.fname
                        },
                        {
                            "key": "Line Number",
                            "value": item.line_number
                        },
                        {
                            "key": "Function",
                            "value": item.func
                        },
                        {
                            "key": "Exception",
                            "value": item.exc
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
                            text: modelData.value  || ""
                        }
                    }
                }
            }
        }
    }
}