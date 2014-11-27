import QtQuick 2.3

import "../generic" as Generic
import "../service/constant.js" as Constant
import "controller.js" as Ctrl

/*
 * Header
 *
 * Description
 *      Main header, used for moving the application
 *      along with closing, minimizing and logo display.
*/
Generic.Rectangle {
    id: root
    
    signal closeClicked
    signal drag(real x, real y)
    signal tabChanged(string name)

    clip: true
    implicitWidth: 400
    height: Constant.size.headerHeight
    states: [
        State {
            name: "systemTab"
            PropertyChanges { target: tab1Id; state: "active"}
            PropertyChanges { target: tab2Id; state: ""}
            PropertyChanges { target: tab3Id; state: ""}
        },
        State {
            name: "overviewTab"
            PropertyChanges { target: tab1Id; state: ""}
            PropertyChanges { target: tab2Id; state: "active"}
            PropertyChanges { target: tab3Id; state: ""}
        },
        State {
            name: "logTab"
            PropertyChanges { target: tab1Id; state: ""}
            PropertyChanges { target: tab2Id; state: ""}
            PropertyChanges { target: tab3Id; state: "active"}
        }
    ]

    // Default state
    onStateChanged: tabChanged(root.state)

    /*
     * Main mouse area
     *
     * Description
     *      Used for moving the window.
    */
    MouseArea {
        property real lastMouseX: 0
        property real lastMouseY: 0

        anchors.fill: parent
        acceptedButtons: Qt.LeftButton
        // propagateComposedEvents: true

        onPressed: {
            lastMouseX = mouseX
            lastMouseY = mouseY
        }

        // Emit change for parents to pick up
        onPositionChanged: {
            root.drag(mouseX - lastMouseX,
                      mouseY - lastMouseY)
        }
    }


    /*
     * Tabs
     *
    */
    Row {
        anchors.fill: parent
        spacing: -2

        Generic.Tab {
            id: tab1Id
            height: parent.height
            image: Constant.image.logo
            width: 50
            onClicked: root.state = "systemTab"
        }

        Generic.Tab {
            id: tab2Id
            height: parent.height
            text: "Overview"
            onClicked: root.state = "overviewTab"
        }

        Generic.Tab {
            id: tab3Id
            height: parent.height
            text: "Log"
            onClicked: root.state = "logTab"
        }
    }


    /*
     * Header buttons
     *
    */
    Row {
        id: headerButtons

        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: Constant.margins.main
        }

        spacing: Constant.margins.alt

        Generic.Button {
            id: closeButton
            source: Constant.image.close
            width: 30
            height: 30

            onClicked: root.closeClicked();
        }
    }

}