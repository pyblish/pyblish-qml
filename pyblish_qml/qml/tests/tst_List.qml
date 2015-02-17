import QtQuick 2.3
import ".."


List {
    id: list

    Component.onCompleted: {
        if (typeof app === "undefined") {
            Constant.textColor = "black"
            Constant.itemColor = "black"

            list.model = Qt.createQmlObject("import QtQuick 2.3; ListModel {}", list);
            list.section.property = "family";

            for (var i = 0; i < 10; i++) {
                list.model.append({
                    "name": "item " + (i + 1),
                    "isToggled": true,
                    "isSelected": false,
                    "family": "napoleon",
                    "currentProgress": 0,
                    "isProcessing": true,
                    "isCompatible": true,
                    "active": true,
                    "hasError": false,
                    "optional": true
                })
            }
        }
    }
}