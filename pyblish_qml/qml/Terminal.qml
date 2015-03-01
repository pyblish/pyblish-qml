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
        textEdit.text = "Logging started %1\n".arg(new Date());
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

        font.family: "Consolas"

        wrapMode: TextEdit.Wrap
        textFormat: TextEdit.AutoText

        onLinkActivated: Qt.openUrlExternally(link)
    }
}