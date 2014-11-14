import QtQuick 2.3

import "../js/modelService.js" as Model


Text {

    FontLoader {
        id: mainFont
        source: "../font/OpenSans-Semibold.ttf"
    }

    color: Model.color.text
    renderType: Text.QtRendering
    font.family: mainFont.name

}