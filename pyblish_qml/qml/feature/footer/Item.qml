import QtQuick 2.3

import "controller.js" as Ctrl
import "../generic" as Generic
import "../service/constant.js" as Constant


Generic.Rectangle {
    id: root

    property alias message: _message
    
    // 0 = Default; 1 = Publishing
    property int mode: 0
    property bool paused: false

    signal publish
    signal pause
    signal stop

    width: 200
    height: Constant.size.footerHeight

    Message {
        id: _message
        anchors.verticalCenter: parent.verticalCenter
    }

    Row {
        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: Constant.margins.main
        }

        spacing: Constant.margins.alt


        Generic.Button {
            source: Constant.image.stop
            visible: mode === 1 ? true : false
            onClicked: root.stop()
        }

        Generic.Button {
            source: Constant.image.pause
            visible: mode === 1 ? true : false
            onClicked: root.pause()
        }

        Generic.Button {
            source: Constant.image.publish

            onClicked: root.publish()

            /*
             * Disable publish-button
            */
            Rectangle {
                anchors.fill: parent
                color: "gray"
                opacity: 0.5
                visible: mode === 0 || paused ? false : true

                MouseArea {
                    // Steal focus from default button
                    anchors.fill: parent
        }}}

}}