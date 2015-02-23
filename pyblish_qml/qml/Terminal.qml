import QtQuick 2.3
import Pyblish 0.1


Flickable {
    id: terminal

    property alias color: textEdit.color

    function echo(line) {
        terminal.contentY = terminal.contentHeight
        textEdit.append(line);
    }

    function clear() {
        textEdit.text = ""
    }

    anchors.fill: parent
    anchors.margins: 5

    contentWidth: textEdit.paintedWidth
    contentHeight: textEdit.paintedHeight

    boundsBehavior: Flickable.DragOverBounds
    flickableDirection: Flickable.VerticalFlick
    clip: true

    TextEdit {
        id: textEdit

        width: terminal.width
        height: terminal.height
        
        readOnly: true

        color: "white"

        text: "Logging started " + Date();
        font.family: "Consolas"

        wrapMode: TextEdit.Wrap
        renderType: Text.NativeRendering
        textFormat: TextEdit.AutoText
    }
}