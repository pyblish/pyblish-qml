/*global Qt, XMLHttpRequest, print, Component*/ // QML features
/*global Constant, Host, Connection*/              // Registered types
/*global root, Log, log*/                       // Id's
/*jslint plusplus: true*/

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
        for (i = 0; i < a.length; ++i) {
            args.push(a[i]);
        }
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
        Constant.port = Connection.port;
        Constant.urlPrefix = Connection.prefix;
    }

    Host.onReady(function () {
        log.debug("Populating model");

        Host.get_instances(function (resp) {
            var isToggled = false;

            resp.forEach(function (item) {
                if (typeof item.publish !== "undefined") {
                    isToggled = item.publish;
                }

                // Append data
                var obj = {
                    name: item.name,
                    family: item.family,
                    isToggled: isToggled,
                    currentProgress: 0,
                    isSelected: false,
                    isProcessing: false,
                    isCompatible: true,
                    hasError: false,
                    hasWarning: false,
                    hasMessage: false,
                    optional: true,
                    errors: [],
                    warnings: [],
                    messages: [],
                };

                root.instancesModel.append(obj);
            });
        });

        Host.get_plugins(function (resp) {

            // Sort plug-ins by their native order
            resp.sort(function (a, b) { return a.order - b.order; });
            resp.forEach(function (item) {

                // Do not include selectors
                if (item.type === "Selector") {
                    return;
                }

                // print(item.name, "is optional", item.optional);

                // Append data
                var obj = {
                    name: item.name,
                    type: item.type,
                    order: item.order,
                    active: item.active,
                    optional: item.optional,
                    families: [],
                    isToggled: true,
                    isSelected: false,
                    isProcessing: false,
                    isCompatible: true,
                    currentProgress: 0,
                    hasError: false,
                    hasWarning: false,
                    hasMessage: false,
                    errors: [],
                    warnings: [],
                    messages: [],
                };

                if (!obj.active) {
                    obj.isToggled = false;
                }

                if (item.hasOwnProperty("families")) {
                    item.families.forEach(function (family) {
                        obj.families.push({"name": family});
                    });
                }

                root.pluginsModel.append(obj);
            });
        });

        // Display list
        root.state = "overviewTab";

    });

    // Make window re-sizable once animation is complete.
    root.startAnimation.stopped.connect(function () {
        root.isStatic = true;
    });

    root.startAnimation.start();

}

function initDeferred() {
    var timer = new Timer();
    timer.interval = 0;
    timer.repeat = false;
    timer.triggered.connect(function () {
        init();
    });
    timer.start();
}



/* 
 * Quit the application, with animation and (optional) delay
 *
*/
function quit(event, delay) {
    root.startAnimation.stop();

    if (event !== null) {
        event.accepted = Constant.closeOk;
    }

    root.quitAnimation.delay = delay || 0;
    root.quitAnimation.stopped.connect(function () {
        Constant.closeOk = true;
        Qt.quit();
    });

    if (!Constant.closeOk) {
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
    Constant.publishStopped = false;
    Constant.publishPaused = false;

    var i;
    [root.instancesModel, root.pluginsModel].forEach(function (model) {
        for (i = 0; i < model.count; ++i) {
            model.get(i).isProcessing = false;
            model.get(i).currentProgress = 0;
        }
    });
}


function pauseHandler() {
    Constant.publishPaused = true;
    root.footer.paused = true;
    setMessage("Pausing..");
}


function stopHandler() {
    Constant.publishStopped = true;

    if (Constant.publishPaused) {
        Constant.publishPaused = false;
        deactivatePublishingMode();
    } else {
        setMessage("Stopping..");
    }
}


/*
 * Find next toggled item in a model
 *
 *
*/
function getNextToggledIndex(index, model) {
    var item;
    for (index; index < model.count; index++) {
        item = model.get(index);
        if (item && item.isToggled) {
            return index;
        }
    }
    return null;
}


/*
 * Trigger next process
 *  Based on the given status, determine whether or
 *  not processing should continue.
 *
*/
function nextProcess(status) {
    var instanceIndex,
        pluginIndex,
        nextInstanceIndex,
        nextPluginIndex;

    instanceIndex = status.instanceIndex;
    pluginIndex = status.pluginIndex;
    nextInstanceIndex = getNextToggledIndex(instanceIndex, root.instancesModel);
    nextPluginIndex = getNextToggledIndex(pluginIndex, root.pluginsModel);

    // If there is no next, we're done
    if (nextInstanceIndex === null || nextPluginIndex === null) {
        return deactivatePublishingMode();
    }

    // If there's been an error, visualise it.
    if (status.errors.length) {
        Constant.publishErrors[status.instance.name] = [];

        status.errors.forEach(function (error) {
            status.instance.hasError = true;

            // Store errors globally
            Constant.publishErrors[status.instance.name].push(error);
            root.logArea.append(JSON.stringify(error, undefined, 2));
        });
    }

    // Has there been any errors at all?
    if (Object.keys(Constant.publishErrors).length) {

        // If next plug-in is an extractor,
        // that means all validators have completed.
        if (root.pluginsModel.get(nextPluginIndex).type === "Extractor") {
            deactivatePublishingMode();
            setMessage("Validation failed");
            return;
        }
    }

    // Publishing stopped.
    if (Constant.publishStopped) {
        deactivatePublishingMode();
        setMessage("Stopped");
        return;
    }

    // Publishing paused, remember where we were.
    if (Constant.publishPaused) {
        Constant.publishPausedPlugin = pluginIndex;
        Constant.publishPausedInstance = instanceIndex;
        setMessage("Paused");
        return;
    }

    process(nextInstanceIndex, nextPluginIndex);
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
function process(instanceIndex, pluginIndex) {
    var instance = root.instancesModel.get(instanceIndex),
        plugin = root.pluginsModel.get(pluginIndex),
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
            Host.get_process(process_id + "?index=" + Constant.lastIndex, function (resp) {

                // Process is still running
                // 
                // - Get log
                // - Present log to user
                if (resp.running === true) {
                    log.debug("Running: " + process_id);
                    Constant.lastIndex = resp.lastIndex;

                // Process is complete
                // 
                // - Update progress bars
                // - Initiate next process
                } else {
                    timer.stop();
                    log.info(plugin.name + " Complete!");

                    resp.messages.forEach(function (message) {
                        // root.logArea.append(JSON.stringify(message, undefined, 2));
                        root.logArea.append(message.message);
                    });

                    instance.isProcessing = false;
                    instanceIndex += 1;

                    if (instanceIndex + 1 > root.instancesModel.count) {
                        instanceIndex = 0;
                        pluginIndex += 1;

                        plugin.isProcessing = false;
                        plugin.currentProgress = 1.0;
                    }

                    if (pluginIndex + 1 > root.pluginsModel.count) {
                        deactivatePublishingMode();
                        return;
                    }

                    log.debug("Next instance: " + instanceIndex);

                    nextProcess({
                        "instanceIndex": instanceIndex,
                        "pluginIndex": pluginIndex,
                        "instance": instance,
                        "plugin": plugin,
                        "errors": resp.errors,
                        "messages": resp.messages,
                    });
                }
            });
        });

        timer.start();
    });
}


function publishHandler() {
    // If publishing was paused, pick up from where it left off.
    Constant.publishErrors = {};

    var i,
        instance;
    for (i = 0; i < root.instancesModel.count; i++) {
        instance = root.instancesModel.get(i);
        instance.hasError = false;
    }

    if (Constant.publishPaused) {
        Constant.publishPaused = false;
        process(Constant.publishPausedInstance,
                Constant.publishPausedPlugin);

    // Otherwise, start from scratch.
    } else {
        activatePublishingMode();
        nextProcess({
            "instanceIndex": 0,
            "pluginIndex": 0,
            "errors": [],
            "messages": [],
        });
    }
}


// function published(status) {
//     setMessage("Published successfully: " + status);
//     quit(null, 1000);
// }


function closeClickedHandler() {
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
}
