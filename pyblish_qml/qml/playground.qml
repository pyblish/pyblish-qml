import QtQuick 2.3
import QtQuick.Controls 1.2

Button {
    id: myButton
    text: "default text"

    Component.onCompleted: {
        if (modelText !== "undefined") {
            myButton.text = modelText;
        }
    }
}