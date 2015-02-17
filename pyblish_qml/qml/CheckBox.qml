import QtQuick 2.3
import "."

MouseArea {
    id: checkBox

    width: 10
    height: 10

    // opacity: active ? 1 : 0.3

    property bool active: true
    property bool checked: false

    property var statuses: {
        "default": "white",
        "selected": Constant.selectedColor,
        "processing": Constant.itemProcessingColor,
        "succeeded": Constant.succeededColor,
        "warning": Constant.warningColor,
        "success": Constant.successColor,
        "error": Constant.errorColor
    }
            
    property string status: "default"

    Rectangle {
        anchors {
            fill: parent
        }

        color: statuses[status]
        opacity: checkBox.checked ? 1 : 0

        z: -1

        Behavior on opacity {
            NumberAnimation {
                duration: 100
            }
        }
    }
}
