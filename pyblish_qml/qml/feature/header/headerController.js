/*global root, Qt*/

"use strict";


/*
 * Close Clicked Handler
 *
*/
function closeClickedHandler() {
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
}
