import QtQuick 2.0
import Pyblish 0.1


Item {
    id: root

    height: 20
    width: parent.width

    property var object: {"isHidden": false}

    property bool checkState: true
    property bool hideState: object.isHidden
    property string text

    property var statuses: {
        "default": "#ddd",
        "processing": Theme.primaryColor,
        "success": Theme.dark.successColor,
        "warning": Theme.dark.warningColor,
        "error": Theme.dark.errorColor
    }

    property string status: {
        if (object.isProcessing)
            return "processing"
        if (object.hasError)
            return "error"
        if (object.hasWarning)
            return "warning"
        if (object.succeeded)
            return "success"
        return "default"
    }

    signal labelClicked
    signal sectionClicked

    Rectangle {
        anchors.fill: parent
        color: Theme.alpha("#000", 0.4)
        opacity: status == "processing" ? 1.0 : 0
        radius: 3

        Rectangle {
            anchors.fill: parent
            color: "transparent"
            border.color: "white"
            border.width: 1
            radius: 3
            visible: status == "processing" ? 1 : 0

            SequentialAnimation on opacity {
                running: true

                NumberAnimation {
                    from: .4
                    to: 1
                    duration: 800
                    easing.type: Easing.InOutElastic
                }
                NumberAnimation {
                    from: 1
                    to: .4
                    duration: 800
                    easing.type: Easing.InOutElastic
                }

                loops: Animation.Infinite
            }
        }
    }

    Rectangle {
        id: iconBackground
        anchors.fill: parent
        anchors.rightMargin: parent.width - height
        opacity: iconMa.containsPress ? 0.25 :
                 iconMa.containsMouse ? 0.15 : 0
    }

    Rectangle {
        id: labelBackground
        anchors.fill: parent
        anchors.leftMargin: height
        opacity: labelMa.containsPress ? 0.25 :
                 labelMa.containsMouse ? 0.15 : 0
    }

    AwesomeIcon {
        id: minusIcon

        name: "minus"
        opacity: !root.hideState ? 0.7: 0
        anchors.verticalCenter: iconBackground.verticalCenter
        anchors.horizontalCenter: iconBackground.horizontalCenter

        size: 9
    }

    AwesomeIcon {
        name: "plus"
        color: statuses[status]
        opacity: root.hideState ? 0.7: 0
        anchors.verticalCenter: iconBackground.verticalCenter
        anchors.horizontalCenter: iconBackground.horizontalCenter

        size: 9
    }

    Label {
        id: label
        text: root.text
        opacity: 0.5
        anchors.verticalCenter: parent.verticalCenter
        anchors.left: iconBackground.right
        anchors.leftMargin: 5
    }

    MouseArea {
        id: iconMa
        anchors.fill: iconBackground
        hoverEnabled: true
        onClicked: root.sectionClicked()
    }

    MouseArea {
        id: labelMa
        anchors.fill: labelBackground
        hoverEnabled: true
        onClicked: root.labelClicked()
    }
}
