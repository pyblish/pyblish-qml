
import QtQuick 2.3
import "." as Generic
import "../service/constant.js" as Constant


Item {
    id: root
    property alias image: imageId.source
    property alias text: textId.text
    property string name

    signal clicked

    implicitWidth: 100
    implicitHeight: Constant.size.headerHeight
    y: 5

    // Behavior on y {
    //     NumberAnimation { duration: 50 }
    // }

    states: [
        State {
            name: "active"
            PropertyChanges { target: root; z: 1; y: 2 }
            PropertyChanges { target: rectangle; color: Constant.color.background; anchors.bottomMargin: 0 }
        }
    ]

    Generic.Rectangle {
        id: rectangle
        anchors.fill: parent
        anchors.bottomMargin: root.y

        // Behavior on anchors.bottomMargin {
        //     NumberAnimation { duration: 50 }
        // }

        /*
         * Hover
         *
        */
        Rectangle {
            anchors.fill: parent
            anchors.margins: 1
            color: "white"
            opacity: maId.containsMouse && root.state !== "active" ? 0.1 : 0.0
        }

        Image {
            id: imageId
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }

        Generic.Text {
            id: textId
            anchors.verticalCenter: parent.verticalCenter
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }

    MouseArea {
        id: maId
        anchors.fill: parent
        hoverEnabled: true

        onClicked: {
            root.clicked(root.name);
        }
    }
}