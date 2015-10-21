import QtQuick 2.3
import QtQuick.Layouts 1.1

import Pyblish 0.1
import Pyblish.ListItems 0.1 as ListItem


MouseArea {
    id: root

    signal beingHidden
    signal toggled(var data)

    /*!
        Fill parent with an invisible layer separating
        the overall application from the currently active
        context menu.
    */
    anchors.fill: parent

    property var children
    property Item logicalParent

    property int menuX: 0
    property int menuY: 0

    property int restWidth: 150
    property int restHeight: 150

    function show() { currentMenuOpenAnimation.start() }
    function hide() { currentMenuCloseAnimation.start() }

    onPressed: hide()

    View {
        id: menu

        property var window: Utils.findRoot(this)

        x: Math.min(menuX, window.width - restWidth)
        y: Math.min(menuY, window.height - restHeight)

        elevation: 1

        width: restWidth
        height: restHeight

        color: "#333"

        ListView {
            anchors.fill: parent

            model: root.children
            interactive: false

            delegate: ListItem.ContextMenuItem {
                text: modelData.label
                active: modelData.active
                checked: true

                height: 25
                width: parent.width

                onPressed: {
                    toggled(modelData)
                    hide()
                }
            }
        }
    }

    PropertyAnimation {
        id: currentMenuOpenAnimation
        properties: "opacity"
        target: menu
        from: 0
        to: 1
        duration: 300
        easing.type: Easing.OutBack
    }

    PropertyAnimation {
        id: currentMenuCloseAnimation
        properties: "opacity"
        target: menu
        from: 1
        to: 0
        duration: 50
        onStopped: {
            root.visible = false
            root.destroy()
            root.beingHidden()
        }
    }
}