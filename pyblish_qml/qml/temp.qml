import QtQuick 2.0
import Pyblish 0.1
import Pyblish.ListItems 0.1 as ListItem
import "Delegates.js" as Delegate

Rectangle {
    color: "brown"
    anchors.fill: parent

    ListView {
        anchors.fill: parent

        model: objModel

        delegate: Loader {
            width: ListView.view.width
            sourceComponent: ListItem.StandardActions {
                text: object.name
                height: 20
                width: parent.width
                active: true
                checked: true
            }
        }
    }
}