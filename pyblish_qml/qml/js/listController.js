/*global listModel, listList*/

"use strict";

var itemClickedHandler,
    itemIndicatorClickedHandler;

/*
 * Item Indicator Clicked Handler
 *
*/
itemIndicatorClickedHandler = function (index) {
    var item = listModel.get(index);
    item.selected = item.selected ? false : true;
};


/*
 * Item Clicked Handler
 *
*/
itemClickedHandler = function (index) {
    listList.currentIndex = index;
    console.log("Expanding item");
};
