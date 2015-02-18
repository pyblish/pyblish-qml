import QtQuick 2.3
import Pyblish 0.1


View {
    id: terminal

    property alias color: textEdit.color

    function echo(line) {
        flickable.contentY = flickable.contentHeight
        textEdit.append(line);
    }

    function clear() {
        textEdit.text = ""
    }

    Flickable {
        id: flickable

        anchors.fill: parent
        anchors.margins: terminal.margins

        contentWidth: textEdit.paintedWidth
        contentHeight: textEdit.paintedHeight

        boundsBehavior: Flickable.DragOverBounds
        flickableDirection: Flickable.VerticalFlick
        clip: true

        TextEdit {
            id: textEdit

            width: terminal.width
            height: terminal.height
            color: "white"
            text: "Logging started " + Date();
            font.family: "Consolas"
            readOnly: true
            wrapMode: TextEdit.Wrap
            renderType: Text.NativeRendering
            textFormat: TextEdit.AutoText
        }
    }
}