/*global Qt, Model, XMLHttpRequest*/
/*global root, listModel, listList, connection*/

"use strict";

var init,
    publish,
    setMessage,
    published,
    get,
    req,
    quit;


req = function (type, address, callback, payload) {
    var xhr = new XMLHttpRequest(),
        endpoint = "http://127.0.0.1:" + connection.port;

    xhr.open(type,
             endpoint + address,
             true); // Asynchronous

    xhr.onreadystatechange = function () {
        if (xhr.readyState === 4) {
            if (xhr.status !== 200) {
                setMessage("Could not communicate with host");
                return;
            }

            console.log("Running callback");
            callback(JSON.parse(xhr.responseText));

        }
    };

    xhr.send(payload || null);
}

/*
 * Init
 *      Retrieve initial data from host
 *
*/
init = function () {
    console.log("Initialising..");

    req("GET", "/instance", function (res) {
        res.forEach(function (item) {

            // Append data
            item.selected = true;

            console.log("Appending: ", item);
            listModel.append(item);
        });
    });
};

setMessage = function (message) {
    root.message.text = message;
    root.message.animation.restart();
    root.message.animation.start();
    console.log(message);
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
    req("POST", "/publish", function (res) {
        published(res);}, JSON.stringify({
            "action": "publish",
            "instances": instances
    }));
};


published = function (status) {
    setMessage("Published successfully: " + status);
    quit(null, 1000);
};


quit = function (event, delay) {
    startAnimation.stop();
    
    if (event !== null) {
        event.accepted = root._closeOk
    }

    root.quitAnimation.delay = delay || 0
    root.quitAnimation.stopped.connect(function () {
        root._closeOk = true;
        Qt.quit();
    });

    if (!root._closeOk) {
        root.quitAnimation.start()
    };

    console.log("Closing");
};