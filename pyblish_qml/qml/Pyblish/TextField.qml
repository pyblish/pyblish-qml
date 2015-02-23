import QtQuick 2.3
import Pyblish 0.1


TextEdit {
    font.family: "Open Sans"
    color: Theme.dark.textColor
    selectByMouse: true
    selectionColor: color
    selectedTextColor: Qt.darker(Theme.dark.textColor, 2)
}