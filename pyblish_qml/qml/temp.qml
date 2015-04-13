import QtQuick 2.3


Rectangle {
    width: 500
    height: 500

    color: "brown"

    List {
        model: app.itemModel
    }
}