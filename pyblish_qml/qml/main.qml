import QtQuick 2.3
import QtQuick.Window 2.2
import "."


Window {
    title: "Pyblish"
    width: 400
    height: 400
    color: Constant.backgroundColor

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
            },

            State {
                name: "loading"

                PropertyChanges {
                    target: label

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

    Label {
        id: label

        anchors.centerIn: parent
        text: ""
        color: "white"

        opacity: 0
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

    FontLoader { id: mainFont; source: "font/OpenSans-Semibold.ttf" }
}
