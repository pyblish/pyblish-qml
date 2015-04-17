import QtQuick 2.3
import Pyblish 0.1
import Pyblish.ListItems 0.1 as ListItem


ListView {
    id: list

    signal itemClicked(int index)
    signal itemDoubleClicked(int index)
    signal actionTriggered(Action action, int index)

    width: 200
    height: 300

    clip: true

    boundsBehavior: Flickable.DragOverBounds
    pixelAligned: true

    delegate: ListItem.StandardActions {
        text: object.name
        active: object.optional
        checked: object.isToggled

        height: 20
        width: parent.width

        status: {
            if (object.isProcessing)
                return "selected"
            if (object.hasError)
                return "error"
            if (object.succeeded)
                return "success"
            return "default"
        }

        onToggled: itemClicked(index)

        actions: [
            Action {
                name: "repair"
                iconName: "wrench"
                enabled: object.hasError && object.hasRepair ? true : false
                onTriggered: actionTriggered(this, index)
            },

            Action {
                name: "enter"
                iconName: "angle-right"
                onTriggered: actionTriggered(this, index)
            }
        ]
    }

    section.delegate: Item {
        height: 20
        width: parent.width

        Item {
            anchors.fill: parent

            Label {
                text: section
                opacity: 0.5
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
