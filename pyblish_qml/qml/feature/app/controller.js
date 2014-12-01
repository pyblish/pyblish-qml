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


function utcToLocalDate(seconds) {
    var d = new Date(0);
    d.setUTCSeconds(seconds);
    return d;
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
    function get_string(a) {
        var string = "",
            i;
        for (i = 0; i < a.length; ++i) {
            string += a[i];
        }
        return string;
    }

    function debug() { return Log.debug(get_string(arguments)); }
    function info() { return Log.info(get_string(arguments)); }
    function warning() { return Log.warning(get_string(arguments)); }
    function error() { return Log.error(get_string(arguments)); }

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

        Host.getInstances(function (resp) {
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
                    active: item.publish,
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

        Host.getPlugins(function (resp) {

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
        root.body.state = "overviewTab";
        root.body.visible = true;

        Host.getApplication(function (resp) {
            resp.connectTime = utcToLocalDate(resp.connectTime);

            var keys = Object.keys(resp);
            keys.sort();
            keys.forEach(function (key) {
                root.system.append(key + ": " + resp[key]);
            });
        });

    });

    // Make window re-sizable once animation is complete.
    root.startAnimation.stopped.connect(function () {
        root.isStatic = true;
    });

    root.startAnimation.start();

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

function deactivatePublishingMode(message) {
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

    if (typeof message !== "undefined") {
        setMessage(message);
    }
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
    while (index < model.count) {
        item = model.get(index);
        if (item && item.isToggled) {
            return index;
        }

        index++;
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

    // Always increment the instance, but only increment
    // the plug-in if there are no more instances left.
    nextPluginIndex = pluginIndex;
    nextInstanceIndex = getNextToggledIndex(instanceIndex + 1, root.instancesModel);

    if (nextInstanceIndex === null) {
        nextInstanceIndex = getNextToggledIndex(0, root.instancesModel);
        nextPluginIndex = getNextToggledIndex(nextPluginIndex + 1, root.pluginsModel);
    }

    if (nextPluginIndex === null) {
        deactivatePublishingMode("Completed successfully");
        return;
    }

    // If there's been an error, visualise it.
    if (status.errors.length) {
        Constant.publishErrors[status.instance.name] = [];

        status.errors.forEach(function (error) {
            status.instance.hasError = true;

            // Store errors globally
            root.terminal.append2(JSON.stringify(error, undefined, 2));
        });
    }

    // Has there been any errors at all?
    if (Object.keys(Constant.publishErrors).length) {

        // If next plug-in is an extractor,
        // that means all validators have completed.
        if (root.pluginsModel.get(nextPluginIndex).type === "Extractor") {
            deactivatePublishingMode("Validation failed");
            return;
        }
    }

    // Publishing stopped.
    if (Constant.publishStopped) {
        deactivatePublishingMode("Stopped");
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
        date,
        incrementSize = 1 / root.pluginsModel.count;

    // Start by posting a process
    Host.postProcesses(instance.name, plugin.name, function (resp) {
        process_id = resp.process_id;

        plugin.isProcessing = true;
        plugin.currentProgress = 1.0;
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
            Host.getProcess(process_id + "?index=" + Constant.lastIndex, function (resp) {

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
                    log.info(plugin.name + " Complete!");
                    timer.stop();

                    // Append message to terminal
                    resp.messages.forEach(function (message) {
                        date = utcToLocalDate(message.created);
                        root.terminal.append2(
                            date.getHours() + ":" + date.getMinutes() + ":" + date.getSeconds()
                                + ": "
                                + message.message
                        );
                    });

                    instance.isProcessing = false;
                    plugin.isProcessing = false;

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

/*
 * Publish Handler
 *  Respond to user choosing to publish
 *
*/
function publishHandler() {
    var i,
        instance,
        startInstance,
        startPlugin;

    // Reset errors
    Constant.publishErrors = {};

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
        startInstance = getNextToggledIndex(0, root.instancesModel);
        startPlugin = getNextToggledIndex(0, root.pluginsModel);

        if (startInstance === null || startPlugin === null) {
            setMessage("Select at least one instance and compatible plug-in to start");
            return;
        }

        activatePublishingMode();
        process(startInstance, startPlugin);
    }
}


function closeClickedHandler() {
    root.state = "closing";
    root.minimumHeight = root.header.height;
    root.startAnimation.stop();
    root.quitAnimation.stopped.connect(Qt.quit);
    root.quitAnimation.start();
}
