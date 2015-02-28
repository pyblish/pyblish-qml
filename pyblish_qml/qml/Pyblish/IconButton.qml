import QtQuick 2.0
import Pyblish 0.1


Button {
    id: icon

    signal triggered

    text: action ? action.name : ""
    icon: action ? action.iconName : ""
    enabled: action ? action.enabled : true

    onTriggered: {
        if (action) action.triggered(icon)
    }

    opacity: enabled ? 1 : 0.6

    property Action action

    onClicked: {
        icon.triggered()
    }
}