.pragma library
"use strict";
/*global Qt, connection*/


var color = {
    "background": Qt.rgba(0.3, 0.3, 0.3),
    "foreground": Qt.rgba(0.6, 0.6, 0.6),
    "text": "white",
    "item": "#6896BB",
    "itemProcessing": "#597221",
    "error": Qt.rgba(1.0, 0.2, 0.2),
};

var size = {
    "windowHeight": 500,
    "windowWidth": 400,
    "windowMinimumWidth": 200,
    "windowMinimumHeight": 200,
    "headerHeight": 40,
    "footerHeight": 40
};

var image = {
    "logo": "../../img/logo-white.png",
    "communication": "../../img/communication.png",
    "publish": "../../img/button-publish.png",
    "pause": "../../img/button-pause.png",
    "stop": "../../img/button-stop.png",
    "close": "../../img/button-close.png",
    "processing": "../../img/processing-small.png",
    "processingError": "../../img/processing-error.png",
};

var margins = {
    "main": 5,
    "alt": 3
};

var closeOk = false;


var port = 0,
    urlPrefix = "";

var publishPaused = false,
    publishStopped = false,
    publishPausedPlugin = 0,   // Current plugin at the time of pause
    publishPausedInstance = 0, // Current instance ..
    lastIndex = 0,
    publishErrors = {};