/*
 * QML entry-point
 *
 * This file is loaded from Python and in turn loads
 * the actual application. The application is then loaded
 * in an asynchronous fashion so as to display the window
 * as quickly as possible.
 *
 * See app.qml for next step.
 *
*/

import QtQuick 2.3
import QtQuick.Window 2.2
import QtQml.StateMachine 1.0


Rectangle {
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

        source: "app.qml"

        onStatusChanged: {
            if (status == Loader.Loading)
                console.time("Polishing")
            if (status == Loader.Ready)
                console.timeEnd("Polishing")
            if (status == Loader.Error)
                errored()
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
