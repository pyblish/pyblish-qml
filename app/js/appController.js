/*global Qt, Model, XMLHttpRequest*/
/*global root, listModel, listList*/

"use strict";

var init,
    publish,
    setMessage;

/*
 * Init
 *      Retrieve initial data from host
 *
*/
init = function () {
    var xhr = new XMLHttpRequest();

    xhr.open("GET",
             "http://127.0.0.1:6000/instance",
             true); // Asynchronous

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status !== 200) {
                setMessage("Could not communicate with host");
                return;
            }

            JSON.parse(xhr.responseText).forEach(function (item) {

                // Append data
                item.selected = true;

                listModel.append(item);
            });
        }
    };

    xhr.send();
};

setMessage = function (message) {
    root.message.text = message;
    root.message.animation.restart();
    root.message.animation.start();
    console.log("Could not communicate with host");
};

/*
 * Publish
 *      Instruct host to perform a publish
 * 
 * Data
 *      {action: actionType,
 *       instances: list of instances}
 *
*/
publish = function () {
    var i,
        xhr,
        item,
        instances = [];

    // Get selected instances from model
    for (i = listModel.count - 1; i >= 0; i--) {
        item = listModel.get(i);

        if (item.selected === true) {
            instances.push({
                name: item.instance,
                plugins: ["plugin1", "plugin2"]
            });
        }
    }

    if (instances.length === 0) {
        setMessage("No instances selected..");
        return;
    }

    // Transmit request
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
};
