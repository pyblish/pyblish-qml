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
    id: root

    property alias view: _listView
    property alias model: _listView.model
    property alias section: _listView.section
    property string hoverDirection: "right"

    signal itemHovered(int index)

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
                anchors.leftMargin: indicatorContainerId.width
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
                id: hoverId
                property bool hovered: false

                x: parent.width
                height: parent.width
                width: parent.height
                anchors.verticalCenter: parent.verticalCenter
                rotation: -90
                gradient: Gradient {
                    GradientStop { position: 0.0; color: "transparent" }
                    GradientStop { position: 1.0; color: "white" }
                }
                opacity: hovered ? 0.1 : 0
                visible: false

                states: [
                    State {
                        name: "hoverFromLeft"
                        PropertyChanges {
                            target: hoverId
                            rotation: 90
                            x: 0
                        }
                    },
                    State {
                        name: "hoverFromRight"
                        PropertyChanges {
                            target: hoverId
                            rotation: -90
                            x: parent.width
                        }
                    }
                ]

                state: hoverDirection === "right" ? "hoverFromRight" : "hoverFromLeft"
            }


            /*
             * Item progress
             *
            */
            Rectangle {

                function calculate_progress(currentProgress) {
                    return (1 - currentProgress) * (parent.width - indicatorContainerId.width)
                }

                anchors.fill: parent
                anchors.rightMargin: calculate_progress(currentProgress)
                anchors.leftMargin: indicatorContainerId.width
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
                        PropertyChanges { target: indicatorCheckboxId; visible: false }
                        PropertyChanges { target: indicatorProcessingId; visible: true }
                        PropertyChanges { target: indicatorProcessingAnimationId; running: true }
                    },

                    // An error has occured, display a little tick-
                    // mark next to it, indicating that there is
                    // errors to inspect within.
                    State {
                        name: "errored"
                        when: hasError
                        PropertyChanges { target: indicatorErroredId; visible: true }
                    },

                    // The item is active and might be toggled
                    State {
                        name: "active"
                        when: active
                        PropertyChanges { target: hoverId; visible: true }
                        PropertyChanges { target: indicatorMouseArea; visible: optional }
                        PropertyChanges { target: indicatorContainerId; opacity: optional ? 1.0 : 0.5 }
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
                    id: indicatorContainerId
                    width: 10
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    // opacity

                    // Outer border
                    Rectangle {
                        id: indicatorCheckboxId
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
                        id: indicatorProcessingId
                        anchors.verticalCenter: parent.verticalCenter
                        source: Constant.imageProcessing
                        visible: false
                        width: 7
                        height: 7

                        NumberAnimation {
                            id: indicatorProcessingAnimationId
                            target: indicatorProcessingId
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
                        id: indicatorErroredId
                        anchors.verticalCenter: parent.verticalCenter
                        color: Constant.errorColor
                        width: 7
                        height: 7
                        visible: false
                    }


                    MouseArea {
                        id: indicatorMouseArea
                        anchors.fill: parent
                        visible: false
                        onClicked: {
                            var item = root.model.get(index);
                            item.isToggled = item.isToggled ? false : true;
                        }
                    }
                }


                GlobalText {
                    id: text
                    text: name
                    anchors.left: indicatorContainerId.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter
                    color: isCompatible && isToggled ? "white" : "gray"

                    Behavior on color {
                        ColorAnimation {
                            duration: 100
            }}}}

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent
                anchors.leftMargin: indicatorContainerId.width

                onClicked: {
                    var item,
                    i;

                    item = root.model.get(index);

                    /* Control-click behavior */
                    if (typeof PyQt !== "undefined") {
                        if (PyQt.queryKeyboardModifiers() === PyQt.ControlModifier) {
                            item.isSelected = item.isSelected ? false : true;

                        } else {
                            for (i = 0; i < root.model.count; ++i) {
                                root.model.get(i).isSelected = false;
                            }
                        }

                        /* Shift-click behaviour (todo) */
                    }
                }
                onEntered: {
                    itemHovered(index);
                    hoverId.hovered = true;
                }
                onExited: {
                    itemHovered(-1);
                    hoverId.hovered = false;
                }
            }
    }}


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

                GlobalText {
                    text: section
                    opacity: 0.5
                    anchors.verticalCenter: parent.verticalCenter
    }}}}

    /*
     * Running standalone
     *
    */
    Component.onCompleted: {
        if (!_listView.model) {
            root.color = Constant.backgroundColor;

            _listView.model = Qt.createQmlObject("import QtQuick 2.3; ListModel {}", root);
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
}}}}