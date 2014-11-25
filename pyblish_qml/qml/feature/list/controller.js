/*global root, print, PyQt, log*/

"use strict";


/*
 * Item Indicator Clicked Handler
 *
*/
function itemIndicatorClickedHandler(index) {
    var item = root.model.get(index);
    item.toggled = item.toggled ? false : true;
}


/*
 * Item Clicked Handler
 *
*/
function itemClickedHandler(index) {
    var item, ii;

    // Control-click behavior
    if (typeof PyQt !== "undefined") {
        if (PyQt.queryKeyboardModifiers() !== PyQt.ControlModifier) {
            for (ii = 0; ii < root.model.count; ++ii) {
                root.model.get(ii).selected = false;
            }
        }

        // Shift-click behaviour (todo)
    }

    item = root.model.get(index);
    item.selected = item.selected ? false : true;
    root.view.currentIndex = index;
    log.debug("Expanding item");
}