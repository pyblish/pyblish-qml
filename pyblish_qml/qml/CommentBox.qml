import QtQuick 2.6
import QtQuick.Layouts 1.1

import Pyblish 0.1

Rectangle {
    id: root
    clip: true
    height: 0

    color: Theme.backgroundColor

    property bool isUp
    property bool isMaximised

    property alias text: textBox.text

    property var readOnly: false

    Behavior on height {
        NumberAnimation {
            duration: 500
            easing.type: Easing.OutQuint
        }
    }

    function up() {
        isUp = true
        textBox.forceActiveFocus()
    }

    function down() {
        isUp = false
        isMaximised = false
    }

    function toggle() {
        isUp ? down() : up()
    }

    View {
        radius: 3
        elevation: -1
        anchors.fill: parent
        anchors.margins: 5
        Layout.fillHeight: true
        Layout.fillWidth: true

        TextEdit {
            id: textBox
            anchors.fill: parent
            anchors.margins: 5
            color: "white"
            selectionColor: "#222"
            selectByMouse: true
            readOnly: root.readOnly
            wrapMode: TextEdit.WordWrap
            clip: true

            Label {
                text: "Comment"
                opacity: 0.5
                visible: parent.length == 0
            }

            font.family: "Open Sans"
            font.weight: Font.Normal

            KeyNavigation.priority: KeyNavigation.BeforeItem

            onTextChanged: app.commenting(text)
        }
    }
}
