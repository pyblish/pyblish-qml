/*global Qt, XMLHttpRequest, print, Component*/ // QML features
/*global Model, Host, Connection*/              // Registered types
/*global root, Log, log*/                       // Id's

"use strict";

/*
 * Generic timer
 *
*/
function Timer() {
    return Qt.createQmlObject("import QtQuick 2.3; Timer {}", root);
}


/*
 * Mock log, replaced if Python is present
 *
*/
function MockLog() {
    function std() {
        return console.log(arguments);
    }

    function debug() {
        return console.log(arguments);
    }

    return {
        debug: debug,
        info: std,
        warning: std,
        error: std,
        critical: std,
    };
}


/*
 * Mimic the console.log argument signature
 * and produce a QStringList which will be passed
 * to Python's logging module.
 *
*/
function PythonLog() {
    function get_args(a) {
        var args = [],
            i;
        for (i = 0; i < a.length; i++) {
            args.push(a[i]);
        };
        return args;
    }

    function debug() { return Log.debug(get_args(arguments)); }
    function info() { return Log.info(get_args(arguments)); }
    function warning() { return Log.warning(get_args(arguments)); }
    function error() { return Log.error(get_args(arguments)); }

    return {
        debug: debug,
        info: info,
        warning: warning,
        error: error,
    };
}


/*
 * Display a graphical message in the UI
 *
*/
function setMessage(message) {
    root.footer.message.text = message;
    root.footer.message.animation.restart();
    root.footer.message.animation.start();
    log.info(message);
}


/*
 * Retrieve initial data from host
 *
*/
function init() {
    if (typeof Connection !== "undefined") {
        log.debug("Connection found, setting port to: " + Connection.port);
        Model.port = Connection.port;
        Model.urlPrefix = Connection.prefix;
    }

    // Make window re-sizable once animation is complete.
    root.startAnimation.stopped.connect(function () {
        root.isStatic = true;
    });

    root.startAnimation.start();

    Host.onReady(function () {
        log.debug("Populating Model");

        Host.get_instances(function (resp) {
            resp.forEach(function (item) {

                // Append data
                var obj = {
                    name: item.name,
                    family: item.family,
                    isToggled: true,
                    isSelected: false,
                    currentProgress: 0,
                    isProcessing: false,
                    isCompatible: true
                };

                root.instancesModel.append(obj);
            });
        });

        Host.get_plugins(function (resp) {

            // Sort plug-ins by their native order
            resp.sort(function (a, b) {return a.order - b.order});

            resp.forEach(function (item) {

                if (item.type === "Selector") {
                    return;
                }

                // Append data
                var obj = {
                    name: item.name,
                    type: item.type,
                    order: item.order,
                    families: [],
                    isToggled: true,
                    isSelected: false,
                    currentProgress: 0,
                    isProcessing: false,
                    isCompatible: true,
                };

                if (item.hasOwnProperty("families")) {
                    item.families.forEach(function (family) {
                        obj.families.push({"name": family});
                    });
                }

                root.pluginsModel.append(obj);
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


/* 
 * Quit the application, with animation and (optional) delay
 *
*/
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
    log.info("Activating publishing mode");

    // Reset progressbars
    var i;
    [root.instancesModel, root.pluginsModel].forEach(function (model) {
        for (i = 0; i < model.count; ++i) {
            model.get(i).isProcessing = false;
            model.get(i).currentProgress = 0;
        }
    });

    root.footer.mode = 1;
}

function deactivatePublishingMode() {
    log.info("Deactivating publishing mode");
    root.footer.mode = 0;
    root.footer.paused = false;
    Model.publishStopped = false;
    Model.publishPaused = false;

    var i;
    [root.instancesModel, root.pluginsModel].forEach(function (model) {
        for (i = 0; i < model.count; ++i) {
            model.get(i).isProcessing = false;
            model.get(i).currentProgress = 0;
        }
    });
}

function publishHandler() {
    // If publishing was paused, pick up from where it left off.
    if (Model.publishPaused) {
        Model.publishPaused = false;
        process(Model.publishPausedInstance, Model.publishPausedPlugin)

    // Otherwise, start from scratch.
    } else {
        activatePublishingMode();
        process(0, 0);
    }


}

function pauseHandler() {
    Model.publishPaused = true;
    root.footer.paused = true;
    setMessage("Pausing..");
}


function stopHandler() {
    Model.publishStopped = true;

    if (Model.publishPaused) {
        Model.publishPaused = false;
        deactivatePublishingMode();
    } else {
        setMessage("Stopping..");
    }
}

/*
 * Main Processing Loop
 *  This is the function which performs isProcessing, and
 *  ultimately publishes the given items in the GUI.
 *
 *  It transmits the physical requests to a host and
 *  updates the GUI with relevant information coming
 *  back from it.
 *
*/
function process(currentInstance, currentPlugin) {
    if (Model.publishStopped) {
        deactivatePublishingMode();
        setMessage("Stopped");
        return;
    }

    // Remember where we were upon pausing
    if (Model.publishPaused) {
        Model.publishPausedPlugin = currentPlugin;
        Model.publishPausedInstance = currentInstance;
        setMessage("Paused");
        return;
    }

    var instance = root.instancesModel.get(currentInstance),
        plugin = root.pluginsModel.get(currentPlugin),
        process_id,
        timer,
        incrementSize = 1 / root.pluginsModel.count;

    // Start by posting a process
    Host.post_processes(instance.name, plugin.name, function (resp) {
        process_id = resp.process_id;

        plugin.isProcessing = true;
        instance.isProcessing = true;
        instance.currentProgress += incrementSize;

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
                    log.debug("Running: " + process_id);

                // Process is complete
                // 
                // - Update progress bars
                // - Initiate next process
                } else {
                    log.info(plugin.name + " Complete!");
                    timer.stop();

                    instance.isProcessing = false;
                    currentInstance += 1;

                    if (currentInstance + 1 > root.instancesModel.count) {
                        currentInstance = 0;
                        currentPlugin += 1;

                        plugin.isProcessing = false;
                        plugin.currentProgress = 1.0;

                    }

                    if (currentPlugin + 1 > root.pluginsModel.count) {
                        deactivatePublishingMode();
                        return print("All plug-ins processed!");
                    }

                    log.debug("Next instance: " + currentInstance);
                    process(currentInstance, currentPlugin);
                }
            });
        });

        timer.start();
    });
}


function published(status) {
    setMessage("Published successfully: " + status);
    quit(null, 1000);
}


function closeClickedHandler() {
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
}
