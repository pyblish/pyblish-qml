"use strict";
/*global Qt, Model, canvasModel, canvasList*/
/*global XMLHttpRequest*/


/*
 * Init
 *  Retrieve initial data from host
 *
*/
function init() {
    var xhr = new XMLHttpRequest();

    xhr.open("GET",
             "http://127.0.0.1:6000/instance",
             true); // Asynchronous

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            JSON.parse(xhr.responseText).forEach(function (item) {
                canvasModel.append(item);
            });
        }
    };

    xhr.send();
}

/*
 * Publish
 *      Instruct host to perform a publish
 * 
 * Data
 *      {action: actionType,
 *       instances: list of instances}
 *
*/
function publish() {

    var i,
        xhr,
        item,
        instances = [];

    // Get selected instances from model
    for (i = canvasModel.count - 1; i >= 0; i--) {
        item = canvasModel.get(i);

        if (item.selected === true) {
            console.log(item.instance, " is selected");
        }

        instances.push({
            name: item.instance,
            plugins: ["plugin1", "plugin2"]
        });
    }

    xhr = new XMLHttpRequest();

    xhr.open("POST",
             "http://127.0.0.1:6000/publish",
             true); // Asynchronous

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            console.log("Done!");
        }
    };

    xhr.send(JSON.stringify({
        "action": "publish",
        "instances": instances
    }));
}

function itemClickedHandler(index) {
    canvasList.currentIndex = index;
}