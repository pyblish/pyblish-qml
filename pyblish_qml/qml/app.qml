import QtQuick 2.3
import QtQuick.Window 2.2

import "feature/generic" as Generic
import "feature/header" as Header
import "feature/footer" as Footer
import "feature/list" as List
import "feature/instances" as Instances
import "feature/plugins" as Plugins
import "feature/animation" as Animation

import "feature/service/constant.js" as Constant
import "feature/service/host.js" as Host

import "feature/app/controller.js" as Ctrl


/*
 * Main window
 *
*/
Window {
    property alias header: headerId
    property alias body: bodyId
    property alias footer: footerId

    property alias terminal: terminalId
    property alias instancesModel: instancesModelId
    property alias pluginsModel: pluginsModelId

    property alias quitAnimation: quitAnimationId
    property alias startAnimation: startAnimationId
    
    property alias state: containerId.state

    property bool isStatic: false
    property var log: new Ctrl.MockLog()

    id: root

    flags: Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint
    color: "transparent"

    width: Constant.size.windowWidth
    height: Constant.size.windowHeight
    minimumWidth: Constant.size.windowMinimumWidth
    minimumHeight: root.isStatic ? Constant.size.windowMinimumHeight : 0

    /*
     * Container
     *  Represents the window, for smoother animations
     *  than animating the OS-level window.
    */
    Generic.Rectangle {
        id: containerId
        width: parent.width
        color: Constant.color.background
        height: headerId.height + footerId.height - 1
        clip: true

        states: [
            State {
                name: "static"
                when: root.isStatic
                PropertyChanges { target: containerId; height: parent.height}
            },
            State {
                name: "closing"
                PropertyChanges { target: connectionText; visible: false }
            }
        ]

        Header.Item {
            id: headerId
            anchors.left: parent.left
            anchors.right: parent.right
            state: "overviewTab" // Default state
            z: 1

            onDrag: {
                root.x += x
                root.y += y
            }

            // When tab changes, alter visibility of body items
            onTabChanged: bodyId.state = name
            onCloseClicked: Ctrl.closeClickedHandler()
        }

        
        Generic.Rectangle {
            id: bodyId

            outwards: false
            visible: false
            clip: true
            anchors.top: headerId.bottom
            anchors.bottom: footerId.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Constant.margins.main

            states: [
                State {
                    name: "systemTab"
                    PropertyChanges { target: systemTabId; visible: true }
                },
                State {
                    // Altering opacity, as opposed to visibility
                    // due to states of overviewTabId not functioning
                    // properly when visiblity is turned off. (E.g. 
                    // items did not return to their default state)
                    name: "overviewTab"
                    PropertyChanges { target: overviewTabId; opacity: 1.0 }
                },
                State {
                    name: "terminalTab"
                    PropertyChanges { target: terminalTabId; visible: true }
                    PropertyChanges { target: bodyId; color: "black" }
                }
            ]

            /*
             * System property page
             *
             *
            */
            Item {
                id: systemTabId
                visible: false
                anchors.fill: parent

                Generic.Text {
                    anchors.centerIn: parent
                    text: "System settings"
                }
            }

            Item {
                id: overviewTabId
                anchors.fill: parent
                opacity: 0

                Instances.List {
                    id: instancesList
                    model: instancesModelId
                    anchors.fill: parent
                    anchors.rightMargin: parent.width / 2
                    section.property: "family"
                    hoverDirection: "left"

                    onItemHovered: {
                        if (index === -1) {
                            pluginsList.validate("");
                        } else {
                            var instance = instancesModelId.get(index)
                            pluginsList.validate(instance.family);
                        }
                    }
                }

                Plugins.List {
                    id: pluginsList
                    model: pluginsModelId
                    anchors.fill: parent
                    anchors.leftMargin: parent.width / 2
                    section.property: "type"
                }
            }


            Item {
                id: terminalTabId
                visible: false
                anchors.fill: parent
                anchors.margins: Constant.margins.main

                Flickable {
                    id: terminalFlickId
                    anchors.fill: parent
                    contentWidth: terminalId.paintedWidth
                    contentHeight: terminalId.paintedHeight
                    boundsBehavior: Flickable.DragOverBounds
                    clip: true


                    TextEdit {
                        id: terminalId

                        function append2(line) {
                            // log.warning("WHHO");
                            print("Setting y to " + terminalFlickId.contentHeight);
                            terminalFlickId.contentY = terminalFlickId.contentHeight
                            terminalId.append(line);
                        }

                        width: terminalFlickId.width
                        height: terminalFlickId.height
                        color: "white"
                        focus: true
                        text: "Logging started " + Date();
                        font.family: "Consolas"
                        readOnly: true
                        wrapMode: TextEdit.Wrap
                        renderType: Text.NativeRendering
        }}}}

        Generic.Text {
            id: connectionText
            text: "No connection"
            anchors.centerIn: parent
            visible: !bodyId.visible
            opacity: 0

            // Slowly fade in
            SequentialAnimation {
                running: true
                PauseAnimation { duration: 1000 }
                NumberAnimation {
                    target: connectionText
                    property: "opacity"
                    duration: 500
                    to: 1.0
        }}}

        Footer.Item {
            id: footerId
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.bottom: parent.bottom
            z: 1

            onPublish: Ctrl.publishHandler();
            onPause: Ctrl.pauseHandler();
            onStop: Ctrl.stopHandler();
    }}


    ListModel { id: instancesModelId }
    ListModel { id: pluginsModelId }


    Animation.OnQuit {
        id: quitAnimationId
        heightTo: headerId.height + footerId.height - 1
        heightFrom: root.height
        heightTarget: containerId
        opacityTarget: root
    }


    Animation.OnStart {
        id: startAnimationId
        heightFrom: headerId.height + footerId.height - 1
        heightTo: root.height
        heightTarget: containerId
    }


    FontLoader {
        id: mainFont
        source: "font/OpenSans-Semibold.ttf"
    }


    Component.onCompleted: {
        // Center window on screen (only relevant on Unix)
        root.x = (Screen.width - root.width) / 2;
        root.y = (Screen.height - root.height) / 2;

        if (typeof Log !== "undefined") {
            root.log = Ctrl.PythonLog();
        }

        Ctrl.init();
    }

    onClosing: Ctrl.quit(close);
}
