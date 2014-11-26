import QtQuick 2.3

/*
 * Start Animation
 *
*/
ParallelAnimation {
    id: startAnimation
    running: false
    alwaysRunToEnd: true

    property int heightFrom: 50
    property int heightTo: 50
    property alias heightTarget: heightAnimation.target

    NumberAnimation {
        id: heightAnimation
        property: "height"
        from: heightFrom
        to: heightTo
        duration: 1000
        easing.type: Easing.InOutQuint
    }
}