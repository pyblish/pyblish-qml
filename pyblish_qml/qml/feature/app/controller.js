/*global Qt, XMLHttpRequest, print, Component*/ // QML features
/*global Model, Host, Connection*/              // Registered types
/*global root, log */                           // Id's

"use strict";

/*
 * Generic timer
 *
*/
function Timer() {
    return Qt.createQmlObject("import QtQuick 2.3; Timer {}", root);
}

/*
 * Mock log, replaced via Python
 *
*/
function Log() {
    function std(msg) {
        return console.log(msg);
    }

    function debug(msg) {
        return console.log(msg);
    }

    return {
        debug: debug,
        info: std,
        warning: std,
        error: std,
        critical: std,
    };
}

function set_message(message) {
    root.footer.message.text = message;
    root.footer.message.animation.restart();
    root.footer.message.animation.start();
    log.debug(message);
}


/*
 * Init
 *  Retrieve initial data from host
 *
*/
function init() {
    if (typeof Connection !== "undefined") {
        log.debug("Connection found, setting port to: " + Connection.port);
        Model.port = Connection.port;
        Model.urlPrefix = Connection.prefix;
    }

    root.startAnimation.start();

    Host.onReady(function () {
        log.debug("Populating Model");

        Host.get_instances(function (resp) {
            resp.forEach(function (item) {

                // Append data
                item.toggled = true;
                item.selected = false;
                item.progress = 0;
                item.processing = false;

                root.instancesModel.append(item);
            });
        });

        Host.get_plugins(function (resp) {
            resp.forEach(function (item) {

                // Append data
                item.toggled = true;
                item.selected = false;
                item.progress = 0;
                item.processing = false;

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

    log.debug("Closing");
}


function activatePublishingMode() {
    // Disable publish button
    // Display stop/pause buttons
    root.footer.publishButton
    log.info("Activating publishing mode");
}

function deactivatePublishingMode() {
    // Activate publish button
    // Hide stop/pause buttons
    log.info("Deactivating publishing mode");
}

function publishHandler() {

    activatePublishingMode();

    // Reset progressbars
    var i;
    [root.instancesModel, root.pluginsModel].forEach(function (model) {
        for (i = 0; i < model.count; ++i) {
            model.get(i).progress = 0;
        }
    });

    process(0, 0);

}

/*
 * Main Processing Loop
 *  This is the function which performs processing, and
 *  ultimately publishes the given items in the GUI.
 *
 *  It transmits the physical requests to a host and
 *  updates the GUI with relevant information coming
 *  back from it.
 *
*/
function process(currentInstance, currentPlugin) {
    var instance = root.instancesModel.get(currentInstance),
        plugin = root.pluginsModel.get(currentPlugin),
        process_id,
        timer,
        incrementSize = 1 / root.pluginsModel.count;

    // Start by posting a process
    Host.post_processes(instance.name, plugin.name, function (resp) {
        process_id = resp.process_id;

        plugin.processing = true;
        instance.processing = true;
        instance.progress += incrementSize;

        timer = new Timer();
        timer.interval = 100;
        timer.repeat = true;
        timer.triggered.connect(function () {

            // The process will yield an ID; the ID is used
            // upon querying the host for information about
            // the submitted process; such as it's current
            // state (either running or not) along with any
            // log messages produced.
            Host.get_process(process_id, function (resp) {

                // Process is still running
                // 
                // - Get log
                // - Present log to user
                if (resp.running === true) {
                    log.info("Running: " + process_id);

                // Process is complete
                // 
                // - Update progress bars
                // - Initiate next process
                } else {
                    log.info(process_id + " Complete!");
                    timer.stop();

                    instance.processing = false;
                    currentInstance += 1;

                    if (currentInstance + 1 > root.instancesModel.count) {
                        currentInstance = 0;
                        currentPlugin += 1;

                        plugin.processing = false;
                        plugin.progress = 1.0;

                    }

                    if (currentPlugin + 1 > root.pluginsModel.count) {
                        deactivatePublishingMode();
                        return print("All plug-ins processed!");
                    }

                    log.info("Next instance: " + currentInstance);
                    process(currentInstance, currentPlugin);
                }
            });
        });

        timer.start();
    });
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
