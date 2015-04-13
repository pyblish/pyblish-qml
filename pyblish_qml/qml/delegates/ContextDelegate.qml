import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    height: bodyItem.height + 10

    body: Row {
        id: delegate

        spacing: 5

        Icon {
            id: icon
            name: "logo-small"
            size: 16
        }

        Column {
            id: content

            spacing: 2

            Label {
                text: item.name + " " + item.pyblishVersion
                style: "title"
                elide: Text.ElideRight
            }

            Repeater {
                model: [
                {
                    "key": "Python",
                    "value": item.pythonVersion.split(" ")[0]
                },
                {
                    "key": "Endpoint",
                    "value": item.endpointVersion
                },
                {
                    "key": "Port",
                    "value": item.port
                },
                {
                    "key": "User",
                    "value": item.user
                },
                {
                    "key": "Host",
                    "value": item.host
                }]

                Row {
                    spacing: 5
                    width: delegate.width - delegate.spacing - icon.width

                    Label {
                        id: _key
                        style: "body2"
                        text: modelData.key
                        backgroundColor: Theme.alpha("white", 0.1)
                    }

                    Label {
                        text: modelData.value
                        elide: Text.ElideRight
                        width: parent.width - _key.width
                    }
                }
            }
        }
    }
}