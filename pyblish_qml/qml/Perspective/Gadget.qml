import QtQuick 2.3
import QtQuick.Layouts 1.1
import Pyblish 0.1


View {
    height: 85

    property string name

    color: Qt.darker(Theme.backgroundColor, 2)

    RowLayout {
        spacing: 10

        anchors.fill: parent
        anchors.rightMargin: 8

        /*!
             _______________________
            |//|                |   |
            |//|                |   |
            |//|________________|___|
        */
        Rectangle {
            color: "#a73f3f"
            width: 25
            height: parent.height

            AwesomeIcon {
                name: "exclamation-circle"
                size: 20
                anchors.horizontalCenter: parent.horizontalCenter
                y: 3
            }
        }

        /*!
             _______________________
            |  |////////////////|   |
            |  |////////////////|   |
            |__|////////////////|___|
        */
        Column {
            Layout.fillWidth: true
            Layout.alignment: Qt.AlignTop
            spacing: 5

            Spacer {}

            Label {
                text: name
                style: "title"
                font.weight: Font.Bold
            }

            Label {
                text: name
                opacity: 0.5
            }
        }

        /*!
             _______________________
            |  |                |///|
            |  |                |///|
            |__|________________|///|
        */
        ColumnLayout {
            spacing: 7

            Repeater {
                model: [
                    {
                        "icon": "wrench",
                        "text": "13/15 passed"
                    },
                    {
                        "icon": "wrench",
                        "text": "ran for 640 ms"
                    },
                    {
                        "icon": "wrench",
                        "text": "about 2 mins ago"
                    }
                ]

                Row {
                    spacing: 10

                    AwesomeIcon {
                        name: modelData.icon
                    }

                    Label {
                        text: modelData.text
                    }
                }
            }
        }
    }
}
