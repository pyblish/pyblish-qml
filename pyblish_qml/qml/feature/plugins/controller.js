"use strict";
/*global root, print*/
/*jslint plusplus: true*/


function contains(a, obj) {
    var i;
    for (i = 0; i < a.count; ++i) {
        if (a.get(i).name === obj) {
            return true;
        }
    }
    return false;
}


function validate(family) {
    var i, plugin;

    for (i = 0; i < root.model.count; ++i) {
        plugin = root.model.get(i);
        plugin.isCompatible = true;

        if (family) {
            if (!contains(plugin.families, family) && !contains(plugin.families, "*")) {
                plugin.isCompatible = false;
            }
        }
    }
}