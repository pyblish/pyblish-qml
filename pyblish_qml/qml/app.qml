import QtQuick 2.3
import QtQuick.Window 2.2

import "feature/generic" as Generic
import "feature/header" as Header
import "feature/footer" as Footer
import "feature/list" as List
import "feature/animation" as Animation

import "feature/service/model.js" as Model
import "feature/service/host.js" as Host

import "feature/app/controller.js" as Ctrl


/*
 * Main window
 *
*/
Window {
    property alias header: header
    property alias body: body
    property alias footer: footer
    property alias instancesModel: instancesModel
    property alias pluginsModel: pluginsModel
    property alias quitAnimation: _quitAnimation
    property alias startAnimation: _startAnimation
    property bool isStatic: false
    property var log: new Ctrl.Log()

    id: root

    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"

    width: Model.size.windowWidth
    height: Model.size.windowHeight
    minimumWidth: Model.size.windowMinimumWidth
    minimumHeight: Model.size.windowMinimumHeight

    /*
     * Container
     *  Represents the window, for smoother animations
     *  than animating the OS-level window.
    */
    Generic.Rectangle {
        id: container
        width: parent.width
        color: Model.color.background
        height: root.isStatic ? parent.height : 0  // Modified with animation
        clip: true

        Header.Item {
            id: header
            z: 1
            anchors.left: parent.left
            anchors.right: parent.right

            onDrag: {
                root.x += x
                root.y += y
            }

            onCloseClicked: Ctrl.closeClickedHandler()
        }
        
        Generic.Rectangle {
            id: body
            visible: false
            outwards: false
            width: parent.width - Model.margins.main * 2

            anchors.top: header.bottom
            anchors.bottom: footer.top
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.margins: Model.margins.main

            List.Item {
                id: instancesList
                model: instancesModel
                anchors.fill: parent
                anchors.rightMargin: parent.width / 2
                section.property: "family"
            }

            List.Item {
                id: pluginsList
                model: pluginsModel
                anchors.fill: parent
                anchors.leftMargin: parent.width / 2
                section.property: "type"
        }}

        Footer.Item {
            id: footer
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom

            onPublish: Ctrl.publishHandler();
        }

        Generic.Text {
            id: connectionText
            text: "No connection"
            anchors.centerIn: parent
            visible: !body.visible
    }}


    ListModel { id: instancesModel }
    ListModel { id: pluginsModel }


    Animation.OnQuit {
        id: _quitAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }


    Animation.OnStart {
        id: _startAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }


    Component.onCompleted: {
        // Center window on screen (only relevant on Unix)
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;

        if (typeof Log !== "undefined") {
            root.log = Log;
        }

        Ctrl.init();
    }

    onClosing: Ctrl.quit(close);
}
