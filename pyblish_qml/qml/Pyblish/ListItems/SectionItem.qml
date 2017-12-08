import QtQuick 2.0
import Pyblish 0.1


Item {
    id: root

    height: 20
    width: parent.width

    property bool checkState: true
    property bool hideState: false
    property string text

    signal labelClicked
    signal sectionClicked

    Rectangle{
        id: background
        anchors.fill: parent
        opacity: ma.containsPress ? 0.5 :
                 ma.containsMouse ? 0.25 : 0
    }

    Icon {
        id: icon
        name: "chevron-down-white"
        anchors.verticalCenter: parent.verticalCenter
        anchors.rightMargin: 5
        size: 10
        rotation: root.hideState ? -90: 0
    }

    Label {
        id: label
        text: root.text
        opacity: label_ma.containsPress ? 1 :
                 label_ma.containsMouse ? 0.75 : 0.5
        anchors.verticalCenter: icon.verticalCenter
        anchors.left: icon.right
        anchors.leftMargin: 5
    }

    MouseArea{
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        onClicked: root.sectionClicked()
    }

    MouseArea{
        id: label_ma
        anchors.fill: label
        hoverEnabled: true
        onClicked: root.labelClicked()
    }
}
