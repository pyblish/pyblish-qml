import QtQuick 2.3
import QtQuick.Controls 2.3 as Control
import Pyblish 0.1

Control.SpinBox {
    id: spinBox
    editable: true
    font.family: mainFont.name
    background: Item {}

    contentItem: TextInput {
        text: spinBox.textFromValue(spinBox.value, spinBox.locale)
        font: spinBox.font
        color: Theme.dark.textColor
        selectionColor: Theme.accentColor
        horizontalAlignment: Qt.AlignHCenter
        verticalAlignment: Qt.AlignVCenter
        readOnly: !spinBox.editable
        validator: spinBox.validator
        inputMethodHints: Qt.ImhFormattedNumbersOnly
    }
}