import QtQuick 2.3
import Pyblish 0.1
import Pyblish.ListItems 0.1 as ListItem


ListView {
    id: list

    signal itemHovered(int index)
    signal itemToggled(int index)
    signal itemClicked(int index)
    signal itemDoubleClicked(int index)

    width: 200
    height: 300

    clip: true

    boundsBehavior: Flickable.StopAtBounds

    delegate: ListItem.Standard {
        text: name
        active: optional
        checked: isToggled

        height: 20
        width: parent.width

        status: {
            if (isProcessing)
                return "selected"
            if (hasError)
                return "error"
            if (succeeded)
                return "success"
            return "default"
        }

        onClicked: list.itemClicked(index)
        onDoubleClicked: list.itemDoubleClicked(index)
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
