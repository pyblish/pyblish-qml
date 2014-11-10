/*global canvasModel, canvasList*/

"use strict";

var itemClickedHandler,
    itemIndicatorClickedHandler;

/*
 * Item Indicator Clicked Handler
 *
*/
itemIndicatorClickedHandler = function (index) {
    var item = canvasModel.get(index);
    item.selected = item.selected ? false : true;
};


/*
 * Item Clicked Handler
 *
*/
itemClickedHandler = function (index) {
    canvasList.currentIndex = index;
    console.log("Expanding item");
};
