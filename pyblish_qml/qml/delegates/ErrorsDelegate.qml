import QtQuick 2.3
import "../Delegates.js" as Delegates


BaseGroupDelegate {
    gutter: true

    item: Column {
        Repeater {
            model: modelData.model

            Loader {
                width: parent.width
                sourceComponent: Delegates.components[object.type]
            }
        }
    }
}