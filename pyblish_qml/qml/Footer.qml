import QtQuick 2.3
import Pyblish 0.1


View {
    id: footer

    property alias message: __message
    
    // 0 = Default; 1 = Publishing; 2 = Finished
    property int mode: 0
    property bool paused: false

    signal publish
    signal pause
    signal stop
    signal reset
    signal save

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

        // Button {
        //     elevation: 1

        //     icon: "button-save"
        //     onClicked: footer.save()
        // }

        Button {
            elevation: 1

            icon: "button-stop"
            visible: mode === 1 ? true : false
            onClicked: footer.stop()
        }

        Button {
            elevation: 1

            icon: "button-reset"
            visible: mode == 0 || mode == 2 ? true : false
            onClicked: footer.reset()
        }

        Button {
            elevation: 1

            icon: "button-publish"

            onClicked: footer.publish()

            /*
             * Disable publish-button
            */
            Rectangle {
                anchors.fill: parent
                color: "gray"
                opacity: 0.5
                visible: mode == 0 ? false : true

                MouseArea {
                    // Steal focus from default button
                    anchors.fill: parent
                }
            }
        }
    }
}