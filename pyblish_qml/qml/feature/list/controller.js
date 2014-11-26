/*global root, print, PyQt*/
/*jslint plusplus: true*/

"use strict";


/*
 * Item Indicator Clicked Handler
 *
*/
function itemIndicatorClickedHandler(index) {
    var item = root.model.get(index);
    item.isToggled = item.isToggled ? false : true;
}


/*
 * Item Clicked Handler
 *
*/
function itemClickedHandler(index) {
    var item,
        i;

    item = root.model.get(index);

    // Control-click behavior
    if (typeof PyQt !== "undefined") {
        if (PyQt.queryKeyboardModifiers() === PyQt.ControlModifier) {
            item.isSelected = item.isSelected ? false : true;

        } else {
            for (i = 0; i < root.model.count; ++i) {
                root.model.get(i).isSelected = false;
            }
        }

        // Shift-click behaviour (todo)
    }
}
