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

    Rectangle {
        anchors {
            fill: parent
        }

        color: checkView.statuses[typeof checkView.status !== "undefined" ? checkView.status : "default"]
        opacity: checkView.checked ? 1 : 0

        z: -1

        Behavior on opacity {
            NumberAnimation {
                duration: 100
            }
        }
    }
}
