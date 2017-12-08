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
        id: iconBackground
        width: 20
        anchors.bottom: parent.bottom
        anchors.top: parent.top
        opacity: ma.containsPress ? 0.5 :
                 ma.containsMouse ? 0.25 : 0
    }

    Rectangle{
        id: labelBackground
        anchors.bottom: parent.bottom
        anchors.top: parent.top
        anchors.left: iconBackground.right
        anchors.right: parent.right
        opacity: label_ma.containsPress ? 0.5 :
                 label_ma.containsMouse ? 0.25 : 0
    }

    AwesomeIcon {
        name: "plus"
        opacity: !root.hideState ? 0.5: 0

        anchors.verticalCenter: iconBackground.verticalCenter
        anchors.horizontalCenter: iconBackground.horizontalCenter

        size: 10
    }

    AwesomeIcon {
        name: "minus"
        opacity: root.hideState ? 0.5: 0

        anchors.verticalCenter: iconBackground.verticalCenter
        anchors.horizontalCenter: iconBackground.horizontalCenter

        size: 10
    }

    Label {
        id: label
        text: root.text
        opacity: 0.5
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: iconBackground.right
        anchors.leftMargin: 5
    }

    MouseArea{
        id: ma
        anchors.fill: iconBackground
        hoverEnabled: true
        onClicked: root.sectionClicked()
    }

    MouseArea{
        id: label_ma
        anchors.fill: labelBackground
        hoverEnabled: true
        onClicked: root.labelClicked()
    }
}
