/*global Qt, Model, XMLHttpRequest*/
/*global root, instancesModel, listList, Host*/
/*global print, quit, connection*/

"use strict";


function setMessage(message) {
    root.message.text = message;
    root.message.animation.restart();
    root.message.animation.start();
    print(message);
}


/*
 * Init
 *      Retrieve initial data from host
 *
*/
function init() {
    if (typeof connection !== "undefined") {
        Model.port = connection.port;
    }

    Host.onReady(function () {
        print("Populating Model");

        Host.get_instances(function (resp) {
            print(resp);
            resp.forEach(function (item) {

                // Append data
                item.selected = true;

                print("Appending: ", item);
                instancesModel.append(item);
            });
        });
    });
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
    print("Publishing!");
}


function published(status) {
    setMessage("Published successfully: " + status);
    quit(null, 1000);
}


function quit(event, delay) {
    root.startAnimation.stop();

    if (event !== null) {
        event.accepted = Model.closeOk;
    }

    root.quitAnimation.delay = delay || 0;
    root.quitAnimation.stopped.connect(function () {
        Model.closeOk = true;
        Qt.quit();
    });

    if (!Model.closeOk) {
        root.quitAnimation.start();
    }

    print("Closing");
}