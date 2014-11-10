import QtQuick 2.3

/*
 * Start Animation
 *
*/
ParallelAnimation {
    id: startAnimation
    running: false

    property int height: 50
    property alias heightTarget: heightAnimation.target
    property alias opacityTarget: opacityAnimation.target

    NumberAnimation {
        id: opacityAnimation
        property: "opacity"
        from: 0
        to: 1
        duration: 500
        easing.type: Easing.OutQuint
    }

    NumberAnimation {
        id: heightAnimation
        property: "height"
        from: root.height / 2
        to: root.height
        duration: 1000
        easing.type: Easing.OutQuint
    }
}