import QtQuick 2.3
import ".."


Terminal {
    id: terminal

    color: "black"

    Component.onCompleted: {
        terminal.echo("Hello, World!")
    }
}