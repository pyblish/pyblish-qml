/*! QML Application
 *
 * This file represents the highest-level of content in the
 * presentation-layer of Pyblish QML.
 *
*/

import QtQuick 2.3
import QtQuick.Controls 1.3

import Pyblish 0.1
import Perspective 0.1 as Perspective


StackView {
    id: stack

    /*! Setup next stack
     *
     * Format relevant proxy-models to display information
     * relevant to the currently entered item.
    */
    function setup(item, commenting) {
        app.recordProxy.clear_inclusion()
        app.recordProxy.add_inclusion("type", "record")
        app.recordProxy.add_inclusion(item.itemType, item.name)

        app.errorProxy.clear_inclusion()
        app.errorProxy.add_inclusion("type", "error")
        app.errorProxy.add_inclusion(item.itemType, item.name)

        var otherItem = item.itemType == "instance" ? "plugin" : "instance"
        app.itemProxy.clear_inclusion()
        app.itemProxy.add_inclusion("itemType", otherItem)

        stack.push({
            item: perspective,
            properties: {
                "item": item,
                "overview": overview,
                "commenting": commenting,
            }
        })
    }

    initialItem: Overview {
        id: overview
        width: stack.width
        height: stack.height

        onCommentEntered: setup(app.instanceProxy.item(index), true)
        onInstanceEntered: setup(app.instanceProxy.item(index), false)
        onPluginEntered: setup(app.pluginProxy.item(index), false)
    }

    Component {
        id: perspective
        Perspective.Page {}
    }
}
