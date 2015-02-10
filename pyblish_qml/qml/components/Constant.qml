pragma Singleton
import QtQuick 2.3


QtObject {
    // Colors
    property color backgroundColor: Qt.rgba(0.3, 0.3, 0.3)
    property color foregroundColor: Qt.rgba(0.6, 0.6, 0.6)
    property color textColor: "white"
    property color itemColor: "#6896BB"
    property color itemProcessingColor: "#597221"
    property color errorColor: Qt.rgba(1.0, 0.2, 0.2)
    
    // Sizes
    property int windowHeight: 500
    property int windowWidth: 400
    property int windowMinimumWidth: 200
    property int windowMinimumHeight: 200
    property int headerHeight: 40
    property int footerHeight: 40

    // Images
    property string imageLogo: "../img/logo-white.png"
    property string imageLogoColor: "img/logo-small.png"
    property string imageCommunication: "../img/communication.png"
    property string imagePublish: "../img/button-publish.png"
    property string imagePause: "../img/button-pause.png"
    property string imageStop: "../img/button-stop.png"
    property string imageClose: "../img/button-close.png"
    property string imageProcessing: "../img/processing-small.png"
    property string imageProcessingError: "../img/processing-error.png"

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
}