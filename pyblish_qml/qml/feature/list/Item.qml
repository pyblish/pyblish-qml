import QtQuick 2.3
import QtGraphicalEffects 1.0

import "../generic" as Generic
import "../service/model.js" as Model
import "../list/controller.js" as Ctrl


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
    width: 200
    height: 300
    clip: true
    color: "transparent"

    property alias view: listView
    property alias model: listView.model
    property alias section: listView.section
    property color itemColor: "#6896BB"


    ListView {
        id: listView
        focus: true
        anchors.fill: parent
        anchors.margins: Model.margins.main
        spacing: 1

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
                anchors.rightMargin: selected ? 0 : parent.width
                anchors.leftMargin: indicatorContainer.width
                color: itemColor
                opacity: selected ? 0.2 : 0

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

                anchors.fill: parent
                anchors.leftMargin: indicatorContainer.width
                color: "transparent"
                opacity: hovered ? 0.1 : 0
                border.width: 1
                border.color: "white"
            }


            /*
             * Item progress
             *
            */
            Rectangle {

                function calculate_progress(progress) {
                    return (1 - progress) * (parent.width - indicatorContainer.width)
                }

                anchors.fill: parent
                anchors.rightMargin: calculate_progress(progress)
                anchors.leftMargin: indicatorContainer.width
                color: itemColor
                opacity: 0.5

                Behavior on anchors.rightMargin {
                    NumberAnimation {
                        duration: 300
                        easing.type: Easing.OutCubic
                    }
                }
            }

            /*
             * Item processing
             *
            */
            Rectangle {
                id: processingRect
                property int processingSpeed: 800

                width: processing ? 10 : 0
                height: parent.height
                color: itemColor
                opacity: 1

                SequentialAnimation {
                    id: _processingAnimation
                    loops: Animation.Infinite
                    running: processing

                    NumberAnimation {
                        target: processingRect
                        property: "x"
                        from: indicatorContainer.width
                        to: parent.width - processingRect.width
                        duration: processingRect.processingSpeed
                    }

                    NumberAnimation {
                        target: processingRect
                        property: "x"
                        from: parent.width - processingRect.width
                        to: indicatorContainer.width
                        duration: processingRect.processingSpeed
                    }
                }

                Behavior on width {
                    NumberAnimation {
                        duration: 100
                        easing.type: Easing.OutCubic
                    }
                }
            }

            Item {
                anchors.top: parent.top
                anchors.bottom: parent.bottom

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
                Rectangle {
                    id: indicatorContainer
                    color: "transparent"
                    anchors.top: parent.top
                    anchors.bottom: parent.bottom
                    width: 10

                    Rectangle {
                        id: indicator

                        Behavior on width {
                            NumberAnimation {
                                duration: 300
                                easing.type: Easing.OutQuint
                        }}

                        anchors {
                            top: parent.top
                            bottom: parent.bottom
                            left: parent.left
                        }

                        width: toggled ? 1 : 0
                        color: "yellow"
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: Ctrl.itemIndicatorClickedHandler(index)
                        onEntered: indicator.width = 5
                        onExited: indicator.width = toggled ? 1 : 0
                }}

                Generic.Text {
                    id: text
                    text: name
                    anchors.left: indicatorContainer.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter

                }}

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent
                anchors.leftMargin: indicatorContainer.width

                onClicked: Ctrl.itemClickedHandler(index)
                onEntered: hover.hovered = true
                onExited: hover.hovered = false
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

                Generic.Text {
                    id: text
                    renderType: Text.QtRendering
                    text: section
                    opacity: 0.5
                    anchors.verticalCenter: parent.verticalCenter
    }}}}

    /*
     * Running standalone
     *
    */
    Component.onCompleted: {
        if (!listView.model) {
            root.color = Model.color.background;
            listView.model = Qt.createQmlObject("import QtQuick 2.3; ListModel {}", root);
            listView.section.property = "family";

            var data = {
                "toggled": false,
                "selected": false,
                "family": "napoleon",
                "progress": 0.4,
            };

            for (var i = 0; i < 10; i++) {
                var clone = JSON.parse(JSON.stringify(data));
                clone.name = "item " + (i + 1);
                listView.model.append(clone)
            }
        }
    }
}