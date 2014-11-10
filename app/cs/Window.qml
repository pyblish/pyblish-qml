import QtQuick 2.3
import QtQuick.Controls 1.2
import QtQuick.Window 2.2

import "../js/modelService.js" as Model
import "../cs" as Cs


Window {
    id: root
    flags: Qt.FramelessWindowHint

    Cs.Rectangle {
        anchors.fill: parent
        color: Model.color.background
    }

    Component.onCompleted: {
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;
    }
}
