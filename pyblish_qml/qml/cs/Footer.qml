import QtQuick 2.3

import "../cs" as Cs
import "../js/modelService.js" as Model
import "../js/footerController.js" as Ctrl

Cs.Rectangle {
    property alias message: message

    id: root

    width: 200
    height: Model.size.footerHeight

    Cs.Message {
        id: message
    }

    Row {
        id: headerButtons

        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: Model.margins.main
        }

        spacing: Model.margins.alt

         Cs.Button {
            id: publishButton
            source: Model.image.publish
            width: 30
            height: 30

            onClicked: Ctrl.publish();
        }
    }
}