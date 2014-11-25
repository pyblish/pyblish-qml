/*global root, print, PyQt*/

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

    if (!item.isSelected) {
        root.itemSelected(index);
    }

    // Control-click behavior
    if (typeof PyQt !== "undefined") {
        if (PyQt.queryKeyboardModifiers() !== PyQt.ControlModifier) {
            for (i = 0; i < root.model.count; ++i) {
                root.model.get(i).isSelected = false;
            }
        }

        // Shift-click behaviour (todo)
    }

    item.isSelected = item.isSelected ? false : true;

}


function validate(family) {
    function contains(a, obj) {
        var i;
        for (i = 0; i < a.count; ++i) {
            if (a.get(i).name === obj) {
                return true;
            }
        }
        return false;
    }

    var i, plugin;
    for (i = 0; i < root.model.count; ++i) {
        plugin = root.model.get(i);
        plugin.isCompatible = true;

        if (!contains(plugin.families, family)) {
            plugin.isCompatible = false;
        }
    }
}