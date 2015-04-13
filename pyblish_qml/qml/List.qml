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

    delegate: ListItem.StandardActions {
        text: item.name
        active: item.optional
        checked: item.isToggled

        height: 20
        width: parent.width

        status: {
            if (item.isProcessing)
                return "selected"
            if (item.hasError)
                return "error"
            if (item.succeeded)
                return "success"
            return "default"
        }

        onToggled: list.itemClicked(index)

        actions: [
            Action {
                name: "repair"
                iconName: "wrench"
                enabled: item.hasError && item.hasRepair ? true : false
                onTriggered: list.actionTriggered(this, index)
            },

            Action {
                name: "explore"
                iconName: "angle-right"
                onTriggered: list.actionTriggered(this, index)
            }
        ]
    }

    section.delegate: Item {
        height: 20
        width: parent.width

        Item {
            anchors.fill: parent

            Label {
                text: item.section
                opacity: 0.5
                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }
}
