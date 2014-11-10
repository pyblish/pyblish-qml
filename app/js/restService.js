"use strict";
/*global Qt*/

// .import "js/modelService.js" as Model


var addInstance = function (instance) {
    console.log("Appending instance: ", instance);
    Model.append(instance);
};

var printSomething = function (something) {
    console.log(something);
};
