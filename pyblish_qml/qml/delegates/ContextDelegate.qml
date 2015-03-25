import QtQuick 2.3
import Pyblish 0.1


BaseDelegate {
    height: bodyItem.height

    body: Row {
        id: delegate

        spacing: 5

        Icon {
            id: icon
            name: "logo-small"
        }

        Column {
            id: content

            spacing: 2

            Label {
                text: name + " " + pyblishVersion
                style: "title"
                elide: Text.ElideRight
            }

            Repeater {
                model: [
                {
                    "key": "Python",
                    "value": pythonVersion.split(" ")[0]
                },
                {
                    "key": "Endpoint",
                    "value": endpointVersion
                },
                {
                    "key": "Port",
                    "value": port
                },
                {
                    "key": "User",
                    "value": user
                },
                {
                    "key": "Host",
                    "value": host
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