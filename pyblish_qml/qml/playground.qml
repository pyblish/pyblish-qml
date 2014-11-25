import QtQuick 2.0
import QtQuick.Controls 1.0
import "model.js" as Model


Button {
    id: button
    text: Model.text

    onClicked: {
        Model.text = "World";
        print("Model.text is:", Model.text)
        print("button.text is:", button.text)
        // Prints Model.text is "World" and button.text is "Hello"
    }
}