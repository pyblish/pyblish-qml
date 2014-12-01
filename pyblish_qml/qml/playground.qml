import QtQuick 2.3
import QtQuick.Window 2.2


Window {
    id: root
    width: 800
    height: 400
    flags: Qt.FramelessWindowHint
    color: Qt.rgba(0, 0, 0, 0.5)

    Rectangle {
        id: header
        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right
        height: close.height
        color: Qt.rgba(0, 0, 0, 0.5)

        MouseArea {
            property real lastMouseX: 0
            property real lastMouseY: 0

            anchors.fill: parent
            acceptedButtons: Qt.LeftButton

            onPressed: {
                lastMouseX = mouseX
                lastMouseY = mouseY
            }

            onPositionChanged: {
                root.x += mouseX - lastMouseX;
                root.y += mouseY - lastMouseY;
            }
        }

        Image {
            id: close
            anchors.right: parent.right
            source: "img/button-close.png"

            MouseArea {
                anchors.fill: parent
                onClicked: Qt.quit();
            }
        }
    }

    Item {
        id: body
        anchors.fill: parent
        anchors.topMargin: header.height

        Loader {
            sourceComponent: button
            onLoaded: {
                item.text = "Assets";
                item.x = 20;
                item.y = 20;
                item.animation.running = true;
            }
        }

        Repeater {
            model: 3
            x: 100
            delegate: button
        }

        Component {
            id: button

            Canvas {
                id: root
                property int wedge: 10
                property string text
                property alias animation: animation
                signal clicked

                width: 100
                height: 50

                ParallelAnimation {
                    id: animation

                    NumberAnimation {
                        target: root
                        property: "x"
                        from: root.x - 20
                        to: root.x
                        duration: 1200
                        easing.type: Easing.OutQuint
                    }

                    NumberAnimation {
                        target: root
                        property: "opacity"
                        from: 0
                        to: 1
                        duration: 200

                    }
                }

                transform: Scale {
                    id: buttonScale
                    origin.x: root.width / 2
                    origin.y: root.height / 2

                    Behavior on xScale { NumberAnimation { duration: 200; easing.type: Easing.OutQuint } }
                    Behavior on yScale { NumberAnimation { duration: 200; easing.type: Easing.OutQuint } }
                }

                states: State {
                    name: "explored"
                    PropertyChanges { target: buttonScale; xScale: 0.75; yScale: 0.75 }
                }

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.fillStyle = Qt.rgba(0.3, 0.3, 0.3)

                    ctx.beginPath()
                    ctx.moveTo(0, 0)

                    ctx.lineTo(width - wedge, 0)
                    ctx.lineTo(width, wedge)
                    ctx.lineTo(width, height)
                    ctx.lineTo(0, height)

                    ctx.closePath()
                    ctx.fill()
                }

                Text {
                    anchors.centerIn: parent
                    text: root.text
                    color: "white"
                }

                MouseArea {
                    id: ma
                    anchors.fill: parent
                    
                    onClicked: {
                        root.clicked();
                    }
                }
            }
        }
    }

}