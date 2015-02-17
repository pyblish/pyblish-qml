import QtQuick 2.3
import "listitems" as ListItem
import "."


ListView {
    id: list

    signal itemHovered(int index)
    signal itemToggled(int index)
    signal itemClicked(int index)

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
                return "processing"
            if (hasError)
                return "error"
            if (succeeded)
                return "succeeded"
            return "default"
        }

        onClicked: {
            list.itemClicked(index)
        }
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
