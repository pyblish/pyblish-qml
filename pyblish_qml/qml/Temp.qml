import QtQuick 2.3

CheckBox {
    id: checkbox
    color: "black"

    onClicked: {
        checkbox.checked = checkbox.checked ? false : true
    }
}