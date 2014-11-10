"use strict";
/*global Qt, Model, canvasModel*/


function init() {
    Model.instances.forEach(function (item) {
        canvasModel.append(item);
    });
}