import QtQuick 2.3
import QtQuick.Window 2.2
import QtQml.StateMachine 1.0


Window {
    title: "Pyblish"

    width: 400
    height: 600

    color: Qt.rgba(0.3, 0.3, 0.3)

    StateMachine {
        id: stateMachine

        running: true

        initialState: loading

        State {
            id: loading

            SignalTransition {
                targetState: running
                signal: loader.loaded
            }

            SignalTransition {
                targetState: errored
                signal: loader.errored
            }
        }

        State {
            id: errored
        }

        State {
            id: running
        }
    }

    Loader {
        id: loader

        signal errored

        anchors.fill: parent
        
        asynchronous: true

        opacity: running.active ? 1 : 0

        Behavior on opacity {
            NumberAnimation {
                duration: 200
            }
        }

        onStatusChanged: {
            if (status == Loader.Loading)
                console.time("Polishing")
            if (status == Loader.Ready)
                console.timeEnd("Polishing")
            if (status == Loader.Error)
                errored()
        }

        Component.onCompleted: {
            loader.sourceComponent = Qt.createComponent(
                Qt.resolvedUrl("Pyblish.qml"),
                Component.Asynchronous)
        }
    }

    Item {
        id: loadingView
        
        anchors.centerIn: parent

        visible: loader.status == Loader.Loading

        Rectangle {
            width: 10
            height: 1

            anchors.centerIn: parent

            color: "white"
            antialiasing: true

            RotationAnimation on rotation {
                duration: 2000
                loops: Animation.Infinite
                from: 0
                to: 360
            }
        }
    }

    Item {
        id: errorView

        anchors.fill: parent
        visible: errored.active

        Text {
            anchors.centerIn: parent
            text: "Oh no!"
            color: "white"
        }
    }
}
