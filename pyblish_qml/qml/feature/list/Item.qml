import QtQuick 2.3

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


    ListView {
        id: listView
        focus: true
        anchors.fill: parent
        anchors.margins: Model.margins.main
        spacing: 1

        delegate: itemDelegate
        section.delegate: sectionDelegate
        section.property: "family"
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

            Rectangle {
                anchors.fill: parent
                anchors.rightMargin: selected ? 0 : parent.width
                anchors.leftMargin: indicatorContainer.width
                color: "#3F7FAB"
                opacity: selected ? 1 : 0

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

            Rectangle {
                id: hover
                anchors.fill: parent
                anchors.leftMargin: indicatorContainer.width
                color: "white"
                opacity: 0

                Behavior on opacity {
                    NumberAnimation {
                        duration: 50
                        easing.type: Easing.OutCubic
            }}}

            MouseArea {
                hoverEnabled: true
                anchors.fill: parent
                anchors.leftMargin: indicatorContainer.width

                onClicked: Ctrl.itemClickedHandler(index)
                onEntered: hover.opacity = 0.05
                onExited: hover.opacity = 0
            }
    }}

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

    /*
     * Running standalone
     *
    */
    Component.onCompleted: {
        if (!listView.model) {
            root.color = Model.color.background;
            listView.model = Qt.createQmlObject("import QtQuick 2.3; ListModel {}", root);;


            [{"name": "item1", "toggled": false, "selected": false},
             {"name": "item2", "toggled": true, "selected": false},
             {"name": "item2", "toggled": true, "selected": false},
             {"name": "item2", "toggled": false, "selected": false},
             {"name": "item3", "toggled": false, "selected": false},
            ].forEach(function (item) {
                listView.model.append(item)
            });
        }
    }
}