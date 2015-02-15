import QtQuick 2.3
import "."


Box {
    id: header
    
    signal tabChanged(string name)

    clip: true
    implicitWidth: 400
    height: Constant.headerHeight

    states: [
        State {
            name: "systemTab"
            PropertyChanges { target: tab1; state: "active"}
            PropertyChanges { target: tab2; state: ""}
            PropertyChanges { target: tab3; state: ""}
        },
        State {
            name: "overviewTab"
            PropertyChanges { target: tab1; state: ""}
            PropertyChanges { target: tab2; state: "active"}
            PropertyChanges { target: tab3; state: ""}
        },
        State {
            name: "terminalTab"
            PropertyChanges { target: tab1; state: ""}
            PropertyChanges { target: tab2; state: ""}
            PropertyChanges { target: tab3; state: "active"}
        }
    ]

    onStateChanged: tabChanged(header.state)


    Row {
        anchors.fill: parent
        spacing: -2

        Tab {
            id: tab1
            height: parent.height
            image: Constant.imageLogo
            width: 50
            onClicked: header.state = "systemTab"
        }

        Tab {
            id: tab2
            height: parent.height
            text: "Overview"
            onClicked: header.state = "overviewTab"
        }

        Tab {
            id: tab3
            height: parent.height
            text: "Terminal"
            onClicked: header.state = "terminalTab"
        }
    }
}