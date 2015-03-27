import QtQuick 2.3
import Pyblish 0.1


Ink {
    id: checkView

    width: 10
    height: 10

    property bool active: true
    property bool checked: false

    property var statuses: {
        "default": "white",
        "selected": Theme.primaryColor,
        "success": Theme.dark.successColor,
        "warning": Theme.dark.warningColor,
        "error": Theme.dark.errorColor
    }

    property string status: "default"

    onStatusChanged: glow.opacity = 1

    Rectangle {
        id: rectangle

        anchors.fill: parent

        color: checkView.statuses[typeof checkView.status !== "undefined" ? checkView.status : "default"]
        opacity: checkView.checked ? 1 : 0

        Behavior on opacity {
            NumberAnimation {
                duration: 100
            }
        }

        Behavior on color {
            ColorAnimation {
                from: "white"
                duration: 100
            }
        }
    }

    Rectangle {
        id: glow

        anchors.fill: parent
        color: "transparent"
        border.color: rectangle.color
        border.width: 1

        // opacity: 0

        // Behavior on opacity {
        //     NumberAnimation {
        //         from: 1
        //         to: 0
        //         duration: 2000
        //         easing.type: Easing.OutQuad
        //     }
        // }
    }
}
