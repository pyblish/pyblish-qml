import QtQuick 2.3

Text {

    FontLoader {
        id: mainFont
        source: "../font/OpenSans-Semibold.ttf"
    }

    color: "white"
    renderType: Text.QtRendering
    font.family: mainFont.name

}