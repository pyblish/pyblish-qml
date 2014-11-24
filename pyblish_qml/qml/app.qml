import QtQuick 2.3
import QtQuick.Window 2.2

import "cs" as Cs
import "js/modelService.js" as Model
import "js/appController.js" as Ctrl
import "js/hostService.js" as Host

/*
 * Main window
 *
 * Properties:
 *      header (alias): Main header
 *      startAnimation (alias): Initial animation
 *      endAnimation (alias): Animation upon quitting
 *      message (alias): Message at the lower left
 *      _closeOk (bool): Used internally
 *
*/
Window {
    property alias header: header
    property alias body: body
    property alias footer: footer
    property alias instancesModel: instancesModel
    property alias instancesList: instancesList
    property alias quitAnimation: _quitAnimation
    property alias startAnimation: _startAnimation
    property bool isStatic: false

    id: root

    flags: Qt.FramelessWindowHint | Qt.Window
    color: "transparent"

    width: Model.size.windowWidth
    height: Model.size.windowHeight
    minimumWidth: Model.size.windowMinimumWidth
    minimumHeight: Model.size.windowMinimumHeight

    Cs.Rectangle {
        id: container
        width: parent.width
        color: Model.color.background
        height: root.isStatic ? parent.height : 0  // Modified with animation

        Cs.Header {
            id: header
            z: 1
            anchors.left: parent.left
            anchors.right: parent.right
        }
        
        Item {
            id: body
            visible: false
            width: parent.width
            anchors.top: header.bottom
            anchors.bottom: footer.top
            anchors.margins: Model.margins.main

            Cs.List {
                id: instancesList
                model: instancesModel
                anchors.fill: parent

            }

            Cs.List {
                id: pluginsList
                model: pluginsModel
        }}

        Cs.Footer {
            id: footer
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            // anchors.margins: Model.margins.main
    }}


    Cs.Text {
        id: connectionText
        text: "No connection"
        anchors.centerIn: parent
        visible: !body.visible
    }

    ListModel { id: instancesModel }
    ListModel { id: pluginsModel }


    FontLoader {
        id: mainFont
        source: "font/OpenSans-Semibold.ttf"
    }


    Cs.QuitAnimation {
        id: _quitAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }


    Cs.StartAnimation {
        id: _startAnimation
        height: header.height
        heightTarget: container
        opacityTarget: root
    }


    Component.onCompleted: {
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;

        root.startAnimation.start();
        Ctrl.init();

    }

    onClosing: Ctrl.quit(close);
}
