import QtQuick 2.3

import "../service/model.js" as Model


Text {

    FontLoader {
        id: mainFont
        source: "../../font/OpenSans-Semibold.ttf"
    }

    color: Model.color.text
    renderType: Text.QtRendering
    font.family: mainFont.name

}