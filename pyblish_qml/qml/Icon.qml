import QtQuick 2.3


Image {
    id: icon

    property string name: ""

    source: {
        if (name == "")
            return ""

        return Qt.resolvedUrl("img/%1.png".arg(name))
    }

    width: sourceSize.Width
    height: sourceSize.Height

    mipmap: true
}