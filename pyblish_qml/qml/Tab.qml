import QtQuick 2.3
import "."


Item {
    id: root
    property alias image: image.source
    property alias text: text.text
    property string name

    signal clicked

    implicitWidth: 100
    implicitHeight: Constant.headerHeight
    y: 5

    states: [
        State {
            name: "active"
            PropertyChanges { target: root; z: 1; y: 2 }
            PropertyChanges { target: rectangle; color: Constant.backgroundColor; anchors.bottomMargin: 0 }
        }
    ]

    Box {
        id: rectangle
        anchors.fill: parent
        anchors.bottomMargin: root.y

        /*
         * Hover
         *
        */
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            color: "white"
            opacity: ma.containsMouse && root.state !== "active" ? 0.1 : 0.0
        }

        Image {
            id: image
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Label {
            id: text
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true

        onClicked: {
            root.clicked(root.name);
        }
    }
}