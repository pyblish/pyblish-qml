/*global root, Qt*/

"use strict";

var closeClickedHandler;


/*
 * Close Clicked Handler
 *
*/
closeClickedHandler = function () {
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
};
