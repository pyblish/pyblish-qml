.pragma library
"use strict";
/*global Qt, connection*/


var color = {
    "background": Qt.rgba(0.3, 0.3, 0.3),
    "foreground": Qt.rgba(0.6, 0.6, 0.6),
    "text": "white"
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
    "publish": "../../img/button-expand.png",
    "close": "../../img/button-close.png",
};

var margins = {
    "main": 5,
    "alt": 3
};

var closeOk = false;


var port = 0,
    urlPrefix = "";
