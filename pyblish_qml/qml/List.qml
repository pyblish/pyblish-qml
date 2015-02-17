import QtQuick 2.3
import "."


/*
 * Instances Item
 *  Represents the main view of instances within the GUI
 *
 *  ______________________
 * | Item                 |
 * | Item                 |
 * | Item                 |
 * | Item                 |
 * |______________________|
 *
 *
*/
Rectangle {
    id: list

    property alias view: _listView
    property alias model: _listView.model
    property alias section: _listView.section
    property string hoverDirection: "right"

    signal itemHovered(int index)
    signal itemToggled(int index)
    signal itemClicked(int index)

    width: 200
    height: 300
    clip: true
    color: "transparent"


    ListView {
        id: _listView
        spacing: 1
        anchors.fill: parent
        anchors.margins: Constant.marginMain
        boundsBehavior: Flickable.StopAtBounds

        delegate: itemDelegate
        section.delegate: sectionDelegate
    }


    /*
     * Item Delegate
     *  Main delegate, used for items in their default state
     *  ______________________
     * |_/_/_/_/_/_/_/_/_/_/_/|
     * |                      |
     * |______________________|
     *
     *
    */
    Component {
        id: itemDelegate

        Item {
            height: 20
            width: parent.width

            /*
             * Item selected
            */
            Rectangle {
                anchors.fill: parent
                anchors.rightMargin: isSelected ? 0 : parent.width
                anchors.leftMargin: indicatorContainer.width
                color: Constant.itemColor
                opacity: isSelected ? 0.2 : 0

                Behavior on opacity {
                    NumberAnimation {
                        duration: 100
                        easing.type: Easing.OutQuint
                    }
                }

                Behavior on anchors.rightMargin {
                    NumberAnimation {
                        duration: 100
                        easing.type: Easing.OutCubic
                    }
                }
            }

            /*
             * Item Hover
             *
            */
            Rectangle {
                id: hover
                property bool hovered: false

                color: "white"
                anchors.fill: parent
                anchors.leftMargin: -5
                opacity: hovered ? 0.1 : 0
                visible: false
            }


            /*
             * Item progress
             *
            */
            Rectangle {

                function calculate_progress(currentProgress) {
                    return (1 - currentProgress) * (parent.width - indicatorContainer.width)
                }

                anchors.fill: parent
                anchors.rightMargin: calculate_progress(currentProgress)
                anchors.leftMargin: indicatorContainer.width
                color: Constant.itemColor
                opacity: 0.5

                Behavior on anchors.rightMargin {
                    NumberAnimation {
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                }
            }

            Item {
                anchors.top: parent.top
                anchors.bottom: parent.bottom
                
                /*
                 * Component States
                 *
                */
                states: [
                    // The item is being processed
                    State {
                        name: "processing"
                        when: isProcessing
                        PropertyChanges {
                            target: indicatorCheckbox

                            visible: false
                        }

                        PropertyChanges {
                            target: indicatorProcessing

                            visible: true
                        }

                        PropertyChanges {
                            target: indicatorProcessingAnimation

                            running: true
                        }

                    },

                    // An error has occured, display a little tick-
                    // mark next to it, indicating that there is
                    // errors to inspect within.
                    State {
                        name: "errored"
                        when: hasError
                        
                        PropertyChanges {
                            target: text

                            color: Qt.lighter(Constant.errorColor, 1.3)
                        }

                        PropertyChanges {
                            target: hover

                            visible: true
                        }

                        PropertyChanges {
                            target: indicatorErrored

                            visible: true
                        }

                    },

                    // The item is active and might be toggled
                    State {
                        name: "active"
                        when: active
                        PropertyChanges {
                            target: hover

                            visible: true
                        }

                        PropertyChanges {
                            target: indicatorContainer

                            opacity: optional ? 1.0 : 0.5
                        }

                    }
                ]

                /*
                 * Indicator/Checkbox Container
                 *  The container takes up a greater space
                 *  than the indicator does visually, so as
                 *  to provide a larger clickable area.
                 *
                 *  ______________________
                 * | |/|                  |
                 * |_|/|__________________|
                 * | |                    |
                 * |_|____________________|
                 *
                */
                Item {
                    id: indicatorContainer
                    width: 10
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    // opacity

                    // Outer border
                    Rectangle {
                        id: indicatorCheckbox
                        anchors.verticalCenter: parent.verticalCenter
                        color: "transparent"
                        border.width: 1
                        border.color: "white"
                        width: 7
                        height: 7
                        visible: true

                        opacity: isToggled ? 1.0 : 0.5

                        // Inner border
                        Rectangle {
                            anchors.fill: parent
                            anchors.margins: isToggled ? 2 : 4
                            color: "white"

                            Behavior on anchors.margins {
                                NumberAnimation {
                                    duration: 200
                                }
                            }
                        }
                    }

                    // Processing..
                    Image {
                        id: indicatorProcessing
                        anchors.verticalCenter: parent.verticalCenter
                        source: Constant.imageProcessing
                        visible: false
                        width: 7
                        height: 7

                        NumberAnimation {
                            id: indicatorProcessingAnimation
                            target: indicatorProcessing
                            property: "rotation"
                            loops: Animation.Infinite
                            duration: 500
                            running: false
                            from: 0
                            to: 360
                        }
                    }

                    // Errored
                    Rectangle {
                        id: indicatorErrored
                        anchors.verticalCenter: parent.verticalCenter
                        color: Constant.errorColor
                        opacity: 0.5
                        width: 7
                        height: 7
                        visible: false
                    }
                }

                Label {
                    id: text
                    text: name
                    anchors.left: indicatorContainer.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: isCompatible && isToggled ? "white" : "gray"

                    Behavior on color {
                        ColorAnimation {
                            duration: 100
                        }
                    }
                }
            }

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent

                onClicked: {
                    itemClicked(index)
                    if (typeof optional !== "undefined" && optional) {
                        itemToggled(index)
                    }

                }
                onEntered: {
                    hover.hovered = true;
                }
                onExited: {
                    hover.hovered = false;
                }
            }
        }
    }


    /*
     * Section Delegate
     *  Visually group items by section
     *  ______________________
     * |Section               |
     * |  / / / / / / / / / / |
     * |                      |
     * |______________________|
     *
    */
    Component {
        id: sectionDelegate

        Item {
            height: 20
            width: parent.width

            Item {
                anchors.fill: parent

                Label {
                    text: section
                    opacity: 0.5
                    anchors.verticalCenter: parent.verticalCenter
    }}}}

    /*
     * Running standalone
     *
    */
    Component.onCompleted: {
        if (typeof app === "undefined") {
            list.color = Constant.backgroundColor;

            _listView.model = Qt.createQmlObject("import QtQuick 2.3; ListModel {}", list);
            _listView.section.property = "family";

            for (var i = 0; i < 10; i++) {
                _listView.model.append({
                    "name": "item " + (i + 1),
                    "isToggled": true,
                    "isSelected": false,
                    "family": "napoleon",
                    "currentProgress": 0,
                    "isProcessing": false,
                    "isCompatible": true,
                    "active": true,
                    "hasError": false,
                    "optional": true
                })
            }
        }
    }
}