import QtQuick 2.0

pragma Singleton


QtObject {
    // Colors
    property color backgroundColor: Qt.rgba(0.3, 0.3, 0.3)
    property color foregroundColor: Qt.rgba(0.6, 0.6, 0.6)
    property color textColor: "white"
    property color itemColor: "#6896BB"
    property color itemProcessingColor: "#59A0DB"
    property color succeededColor: "#82D330"
    property color selectedColor: "#597221"
    property color successColor: "#77AE24"
    property color warningColor: "#597221"
    property color errorColor: Qt.rgba(1.0, 0.2, 0.2)
    
    // Sizes
    property int windowHeight: 500
    property int windowWidth: 400
    property int windowMinimumWidth: 200
    property int windowMinimumHeight: 200
    property int headerHeight: 40
    property int footerHeight: 40

    // Images
    property string imageLogo: "img/logo-white.png"
    property string imageLogoColor: "img/logo-small.png"
    property string imageCommunication: "img/communication.png"
    property string imagePublish: "img/button-publish.png"
    property string imagePause: "img/button-pause.png"
    property string imageStop: "img/button-stop.png"
    property string imageClose: "img/button-close.png"
    property string imageReset: "img/button-reset.png"
    property string imageProcessing: "img/processing-small.png"
    property string imageProcessingError: "img/processing-error.png"

    // Margins
    property int marginMain: 5
    property int marginAlt: 3

    // State
    property bool closeOk: false

    property int port: 0
    property string urlPrefix: ""

    property bool publishPaused: false
    property bool publishStopped: false
    property int publishPausedPlugin: 0
    property int publishPausedInstance: 0
    property int lastIndex: 0
    property var publishErrors: {}

    function alpha(color, alpha) {
        // Make sure we have a real color object to work with (versus a string like "#ccc")
        var realColor = Qt.darker(color, 1)

        realColor.a = alpha

        return realColor
    }
}