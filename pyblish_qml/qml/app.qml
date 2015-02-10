import QtQuick 2.3
import QtQuick.Window 2.2

import "components" as Components
import "js/host.js" as Host
import "js/appController.js" as Ctrl
// import "."


/*
 * Main window
 *
*/
Window {
    property alias header: headerId
    property alias body: bodyId
    property alias footer: footerId

    property alias terminal: terminalId
    property alias system: systemId
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

    width: Components.Constant.windowWidth
    height: Components.Constant.windowHeight
    minimumWidth: Components.Constant.windowMinimumWidth
    minimumHeight: root.isStatic ? Components.Constant.windowMinimumHeight : 0

    /*
     * Container
     *  Represents the window, for smoother animations
     *  than animating the OS-level window.
    */
    Components.Box {
        id: containerId
        width: parent.width
        color: Components.Constant.backgroundColor
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

        Components.Header {
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

        
        Components.Box {
            id: bodyId

            outwards: false
            visible: false
            clip: true
            anchors.top: headerId.bottom
            anchors.bottom: footerId.top
            anchors.left: parent.left
            anchors.right: parent.right
            anchors.margins: Components.Constant.marginMain
            transform: Translate { id: bodyTranslateId } // Used in animation

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

            NumberAnimation {
                id: bodyAnimationId
                target: bodyTranslateId
                property: "x"
                easing.type: Easing.OutQuint
                duration: 500
                from: -5
                to: 0
            }

            onStateChanged: {
                print("Changed");
                bodyAnimationId.stop();
                bodyAnimationId.start();
            }

            /*
             * System property page
             * 
             *  _____________
             * |      |      |
             * |      |      |
             * |      |      |
             * |______|______|
             * |             |
             * |             |
             * |_____________|
             *
            */

            Item {
                id: systemTabId
                visible: false
                anchors.fill: parent
                anchors.margins: Components.Constant.marginMain

                TextEdit {
                    id: systemId
                    width: terminalFlickId.width
                    height: terminalFlickId.height
                    color: "white"
                    font.family: "Open Sans Semibold"
                    readOnly: true
                    wrapMode: TextEdit.Wrap
                    renderType: Text.NativeRendering
                }

                Image {
                    anchors.bottom: parent.bottom
                    anchors.right: parent.right
                    anchors.margins: 20
                    source: Components.Constant.imageLogoColor
                }
            }

            Item {
                id: overviewTabId
                anchors.fill: parent
                opacity: 0

                Components.List {
                    id: instancesList
                    model: instancesModelId
                    anchors.fill: parent
                    anchors.rightMargin: parent.width / 2
                    section.property: "family"
                    hoverDirection: "left"

                    // Upon hovering an instance, fade incompatible plug-ins
                    onItemHovered: {
                        if (index === -1) {
                            pluginsList.validate("");
                        } else {
                            var instance = instancesModelId.get(index)
                            pluginsList.validate(instance.family);
                        }
                    }
                }

                Components.List {
                    id: pluginsList
                    model: pluginsModelId
                    anchors.fill: parent
                    anchors.leftMargin: parent.width / 2
                    section.property: "type"
                    signal validate(string family)

                    onValidate: {
                        function contains(a, obj) {
                            var i;
                            for (i = 0; i < a.count; ++i) {
                                if (a.get(i).name === obj) {
                                    return true;
                                }
                            }
                            return false;
                        }

                        var i, plugin;

                        for (i = 0; i < pluginsList.model.count; ++i) {
                            plugin = pluginsList.model.get(i);
                            plugin.isCompatible = true;

                            if (family) {
                                if (!contains(plugin.families, family) && !contains(plugin.families, "*")) {
                                    plugin.isCompatible = false;
                                }
                            }
                        }
                    }
                }
            }

            Item {
                id: terminalTabId
                visible: false
                anchors.fill: parent
                anchors.margins: Components.Constant.marginMain

                Flickable {
                    id: terminalFlickId
                    anchors.fill: parent
                    contentWidth: terminalId.paintedWidth
                    contentHeight: terminalId.paintedHeight
                    boundsBehavior: Flickable.DragOverBounds
                    flickableDirection: Flickable.VerticalFlick
                    clip: true


                    TextEdit {
                        id: terminalId

                        function append2(line) {
                            terminalFlickId.contentY = terminalFlickId.contentHeight
                            terminalId.append(line);
                        }

                        width: terminalTabId.width
                        height: terminalTabId.height
                        color: "white"
                        text: "Logging started " + Date();
                        font.family: "Consolas"
                        readOnly: true
                        wrapMode: TextEdit.Wrap
                        renderType: Text.NativeRendering
        }}}}

        Components.GlobalText {
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

        Components.Footer {
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


    SequentialAnimation {
        id: quitAnimationId
        property int delay: 0

        running: false

        PauseAnimation {
            duration: quitAnimationId.delay
        }

        NumberAnimation {
            property: "height"
            from: root.height
            to: headerId.height + footerId.height - 1
            duration: 400
            target: containerId
            easing.type: Easing.OutCubic
        }

        PauseAnimation {
            duration: 50
        }

        NumberAnimation {
            id: opacityAnimation
            property: "opacity"
            target: root
            to: 0
            duration: 200
        }
    }


    ParallelAnimation {
        id: startAnimationId
        property int heightFrom: 50
        property int heightTo: 50

        running: false
        alwaysRunToEnd: true

        NumberAnimation {
            property: "height"
            from: headerId.height + footerId.height - 1
            to: root.height
            duration: 1000
            target: containerId
            easing.type: Easing.InOutQuint
        }
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
