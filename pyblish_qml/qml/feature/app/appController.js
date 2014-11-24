/*global Qt, XMLHttpRequest, print*/            // QML features
/*global Model, Host, Connection*/              // Registered types
/*global root*/                                 // Id's

"use strict";


function setMessage(message) {
    root.footer.message.text = message;
    root.footer.message.animation.restart();
    root.footer.message.animation.start();
    console.debug(message);
}


/*
 * Init
 *      Retrieve initial data from host
 *
*/
function init() {
    if (typeof Connection !== "undefined") {
        Model.port = Connection.port;
    }

    Host.onReady(function () {
        console.debug("Populating Model");

        Host.get_instances(function (resp) {
            resp.forEach(function (item) {

                // Append data
                item.selected = true;

                root.instancesModel.append(item);
            });
        });

        Host.get_plugins(function (resp) {
            resp.forEach(function (item) {

                // Append data
                item.selected = true;

                root.pluginsModel.append(item);
            });
        });

        Host.get_application(function (resp) {
            for (var key in resp) {
                Model.debug[key] = resp[key];
            }
        });

        // Display list
        root.body.visible = true;

    });
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

    console.debug("Closing");
}


function published(status) {
    setMessage("Published successfully: " + status);
    quit(null, 1000);
}
