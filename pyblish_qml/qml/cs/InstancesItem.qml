import QtQuick 2.3

import "../cs" as Cs
import "../js/modelService.js" as Model
import "../js/instancesController.js" as Ctrl


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
Cs.Rectangle {
    id: root
    width: 100
    height: 100
    outwards: false
    clip: true

    property alias view: listView
    property alias model: listView.model

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

                        width: selected ? 1 : 0
                        color: "yellow"
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        onClicked: Ctrl.itemIndicatorClickedHandler(index)
                        onEntered: indicator.width = 5
                        onExited: indicator.width = selected ? 1 : 0
                }}

                Cs.Text {
                    id: text
                    text: name
                    anchors.left: indicatorContainer.right
                    anchors.leftMargin: 5
                    anchors.verticalCenter: parent.verticalCenter

                    MouseArea {
                        hoverEnabled: true
                        anchors.fill: parent

                        onClicked: Ctrl.itemClickedHandler(index)
                        onEntered: hover.opacity = 0.05
                        onExited: hover.opacity = 0
            }}}

            Rectangle {
                id: hover
                anchors.fill: parent
                color: "white"
                opacity: 0

                Behavior on opacity {
                    NumberAnimation {
                        duration: 200
                        easing.type: Easing.OutCubic
    }}}}}

    /*
     * Highlight Delegate
     *  Used for items with focus
     *  ______________________
     * |/ / / / / / / / / / / |
     * | / / / / / / / / / / /|
     * |                      |
     * |______________________|
     *
    */
    Component {
        id: highlightDelegate

        Rectangle {
            color: "#3F7FAB"
            opacity: 0.3
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

                Text {
                    id: text
                    renderType: Text.QtRendering
                    text: section
                    color: "white"
                    opacity: 0.5
                    font.family: mainFont.name
                    anchors.verticalCenter: parent.verticalCenter
    }}}}

    ListView {
        id: listView
        focus: true
        anchors.fill: parent
        anchors.margins: Model.margins.main
        spacing: 1

        delegate: itemDelegate
        highlight: highlightDelegate
        section.delegate: sectionDelegate
        section.property: "family"
}}