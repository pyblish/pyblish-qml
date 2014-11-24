/*global Qt, XMLHttpRequest, print, Component*/ // QML features
/*global Model, Host, Connection*/              // Registered types
/*global root*/                                 // Id's

"use strict";

/*
 * Generic timer
 *
*/
function Timer() {
    var component = Qt.createComponent("Timer.qml");
    return component.createObject(root);
}

function set_message(message) {
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
                item.toggled = true;
                item.selected = false;

                root.instancesModel.append(item);
            });
        });

        Host.get_plugins(function (resp) {
            resp.forEach(function (item) {

                // Append data
                item.toggled = true;
                item.selected = false;

                root.pluginsModel.append(item);
            });
        });

        Host.get_application(function (resp) {
            root.header.pyblishVersion = resp.pyblishVersion;
            root.header.host = resp.host;
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


function publishHandler() {
    process(0, 0);

}

function process(currentInstance, currentPlugin) {
    var instance = root.instancesModel.get(currentInstance),
        plugin = root.pluginsModel.get(currentPlugin),
        process_id,
        timer;

    Host.post_processes(instance.name, plugin.name, function (resp) {
        process_id = resp.process_id;

        timer = new Timer();
        timer.triggered.connect(function () {
            Host.get_process(process_id, function (resp) {

                // Process is still running
                // 
                // - Get log
                // - Present log to user
                if (resp.running === true) {
                    console.debug("Running:", process_id);

                // Process is complete
                // 
                // - Update progress bars
                // - Initiate next process
                } else {
                    console.debug(process_id, "Complete!");
                    timer.stop();

                    currentPlugin += 1;

                    if (currentPlugin + 1 > root.pluginsModel.count) {
                        currentPlugin = 0;
                        currentInstance += 1;
                    }

                    if (currentInstance + 1 > root.instancesModel.count) {
                        return print("All instances processed!");
                    }

                    console.debug("Next plugin:", currentPlugin);
                    process(currentInstance, currentPlugin);
                }
            });
        });

        timer.start();
    });


    // Host.get_process(process_id, function (resp) {
    //     if (resp.running !== true) {
    //     }
    // });
}


function published(status) {
    set_message("Published successfully: " + status);
    quit(null, 1000);
}


function closeClickedHandler() {
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
}
