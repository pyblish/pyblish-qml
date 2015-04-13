import QtQuick 2.3
import QtQuick.Controls 1.3
import Pyblish 0.1


StackView {
    id: stack

    function setup(type, name) {
        app.gadgetProxy.clear_inclusion()
        app.gadgetProxy.add_inclusion("itemType", Utils.toTitleCase(type) + "Item")
        app.gadgetProxy.add_inclusion("name", name)

        app.recordProxy.clear_inclusion()
        app.recordProxy.add_inclusion("type", "record")
        app.recordProxy.add_inclusion(type, name)

        app.errorProxy.clear_inclusion()
        app.errorProxy.add_inclusion("type", "error")
        app.errorProxy.add_inclusion(type, name)
    }

    initialItem: Overview {
        onExplorePlugin: {
            var name = app.pluginProxy.data(index, "name")

            setup("plugin", name)

            stack.push({item: perspective})
        }

        onExploreInstance: {
            var name = app.instanceProxy.data(index, "name")

            setup("instance", name)

            stack.push({item: perspective})
        }
    }

    Component {
        id: perspective

        Perspective {
            // height: stack.height
        }
    }
}
