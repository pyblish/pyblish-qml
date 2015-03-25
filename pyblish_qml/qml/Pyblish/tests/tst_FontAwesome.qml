import QtQuick 2.3
import Pyblish 0.1

Rectangle {
    width: 300
    height: 600

    color: "brown"

    ListView {
        anchors.fill: parent

        model: ["power_off", "music", "th_large"]

        delegate: AwesomeIcon {
            name: modelData
            size: 12
        }
    }
}
