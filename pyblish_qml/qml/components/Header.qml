import QtQuick 2.3
import "."


/*
 * Header
 *
 * Description
 *      Main header, used for moving the application
 *      along with closing, minimizing and logo display.
*/
Box {
    id: root
    
    signal closeClicked
    signal drag(real x, real y)
    signal tabChanged(string name)

    clip: true
    implicitWidth: 400
    height: Constant.headerHeight
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
            name: "terminalTab"
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

        Tab {
            id: tab1Id
            height: parent.height
            image: Constant.imageLogo
            width: 50
            onClicked: root.state = "systemTab"
        }

        Tab {
            id: tab2Id
            height: parent.height
            text: "Overview"
            onClicked: root.state = "overviewTab"
        }

        Tab {
            id: tab3Id
            height: parent.height
            text: "Terminal"
            onClicked: root.state = "terminalTab"
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
            margins: Constant.marginMain
        }

        spacing: Constant.marginAlt

        Button {
            id: closeButton
            source: Constant.imageClose
            width: 30
            height: 30

            onClicked: root.closeClicked();
        }
    }

}