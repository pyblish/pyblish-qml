import QtQuick 2.0
import Pyblish 0.1


MouseArea {
    id: view

    clip: true
    hoverEnabled: enabled
    z: 2

    property int startSize: circular ? width/5 : width/3
    property int middleSize: circular ? width * 3/4 : width - 10
    property int endSize: circular ? centered ? width: width * 3
                                   : width * 1.5

    property Item currentCircle
    property color color: Theme.alpha(Theme.backgroundColor, 0.1)

    property bool circular: false
    property bool centered: false

    onPressed: {
        createTapCircle(mouse.x, mouse.y)
    }

    onCanceled: {
        currentCircle.removeCircle();
    }

    onReleased: {
        currentCircle.removeCircle();
    }

    function createTapCircle(x, y) {
        if (!currentCircle)
            currentCircle = tapCircle.createObject(view, {
                                                       "circleX": centered ? width/2 : x,
                                                       "circleY": centered ? height/2 : y
                                                   });
    }

    Component {
        id: tapCircle

        Item {
            id: circleItem

            anchors.fill: parent

            function removeCircle() {
                if (fillAnimation.running) {
                    fillAnimation.stop()

                    slowCloseAnimation.start()

                    circleItem.destroy(400);
                    currentCircle = null;
                } else {
                    circleItem.destroy(400);
                    closeAnimation.start();
                    currentCircle = null;
                }
            }

            property real circleX
            property real circleY

            property bool closed

            Item {
                id: circleParent
                anchors.fill: parent
                visible: !circular

                Rectangle {
                    id: circleRectangle

                    x: circleItem.circleX - width/2
                    y: circleItem.circleY - height/2

                    property double size

                    width: size
                    height: size
                    radius: size/2

                    opacity: 0
                    color: view.color

                    SequentialAnimation {
                        id: fillAnimation
                        running: true

                        ParallelAnimation {

                            NumberAnimation {
                                target: circleRectangle; property: "size"; duration: 400;
                                from: startSize; to: middleSize; easing.type: Easing.InOutQuad
                            }

                            NumberAnimation {
                                target: circleRectangle; property: "opacity"; duration: 200;
                                from: 0; to: 1; easing.type: Easing.InOutQuad
                            }
                        }
                    }

                    ParallelAnimation {
                        id: closeAnimation

                        NumberAnimation {
                            target: circleRectangle; property: "size"; duration: 400;
                            to: endSize; easing.type: Easing.InOutQuad
                        }

                        NumberAnimation {
                            target: circleRectangle; property: "opacity"; duration: 400;
                            from: 1; to: 0; easing.type: Easing.InOutQuad
                        }
                    }

                    ParallelAnimation {
                        id: slowCloseAnimation

                        SequentialAnimation {

                            NumberAnimation {
                                target: circleRectangle; property: "opacity"; duration: 150;
                                from: 0; to: 1; easing.type: Easing.InOutQuad
                            }

                            NumberAnimation {
                                target: circleRectangle; property: "opacity"; duration: 250;
                                from: 1; to: 0; easing.type: Easing.InOutQuad
                            }
                        }

                        NumberAnimation {
                            target: circleRectangle; property: "size"; duration: 400;
                            to: endSize; easing.type: Easing.InOutQuad
                        }
                    }
                }
            }
        }
    }
}
