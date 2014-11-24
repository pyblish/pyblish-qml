/*global root*/

"use strict";


/*
 * Item Indicator Clicked Handler
 *
*/
function itemIndicatorClickedHandler(index) {
    var item = root.model.get(index);
    item.selected = item.selected ? false : true;
}


/*
 * Item Clicked Handler
 *
*/
function itemClickedHandler(index) {
    root.view.currentIndex = index;
    console.log("Expanding item");
}
