import QtQuick 2.3
import Pyblish 0.1


View {
    id: footer

    property alias message: __message
    
    // 0 = Default; 1 = Publishing; 2 = Finished
    property int mode: 0
    property bool hasComment: false

    signal comment

    width: 200
    height: 40

    Message {
        id: __message
        anchors.verticalCenter: parent.verticalCenter
    }

    Row {
        id: row

        anchors {
            right: parent.right
            top: parent.top
            bottom: parent.bottom
            margins: 5
        }

        spacing: 3

        AwesomeButton {
            elevation: 1

            size: 25
            iconSize: 14

            tooltip: visible ? "Comment.." : ""

            name: hasComment ? "comment" : "comment-o"
            onClicked: footer.comment()
            visible: mode == 0 ? true : false
        }
    }
}