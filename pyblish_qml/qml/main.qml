import QtQuick 2.3
import QtQuick.Window 2.2

Window {
    title: "Pyblish"

    width: 400
    height: 600

    color: Qt.rgba(0.3, 0.3, 0.3)

    Item {
        id: states

        state: loader.status == Loader.Ready
                ? "default" : loader.status == Loader.Error ? "error" : "loading"

        states: [
            State {
                name: "error"

                PropertyChanges {
                    target: errorView

                    opacity: 1
                }
            }
        ]
    }

    Loader {
        id: loader

        anchors.fill: parent
        
        asynchronous: true

        Component.onCompleted: {
            var component = Qt.createComponent(Qt.resolvedUrl("Pyblish.qml"), Component.Asynchronous)
            loader.sourceComponent = component
        }
    }

    Item {
        id: errorView

        anchors.fill: parent
        opacity: 0

        Text {
            anchors.centerIn: parent
            text: "Oh no!"
            color: "white"
        }
    }
}
