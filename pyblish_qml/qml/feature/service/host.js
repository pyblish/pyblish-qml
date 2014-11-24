"use strict";
/*global Model, listModel, print, XMLHttpRequest*/
/*global mockHost, Qt, root, Component*/


// Base is always located on the local machine
var BASE = "http://127.0.0.1:" + Model.port + "/pyblish/v1";

/*
 * MockHTTPRequest communicates with a fake Flask
 * client which emulates a production host.
 *
*/
function MockHTTPRequest() {
    var component = Qt.createComponent("../app/MockHTTPRequest.qml"),
        mhr;

    this.readyState = null;
    this.ERROR = 0;
    this.READY = 1;

    if (component.status === Component.Error) {
        this.readyState = this.ERROR;
        this.errorString = component.errorString;
    } else {
        mhr = component.createObject(root);
        console.assert(mhr !== "undefined", "This file should never fail");

        this.readyState = this.READY;
        this.request = mhr.request;
        this.requested = mhr.requested;
    }
}


function real_request(verb, endpoint, obj, cb) {
    print("Request: " + verb + " " + BASE + (endpoint || ""));

    var xhr = new XMLHttpRequest(),
        data;

    xhr.onreadystatechange = function () {
        print("xhr: on ready state change: " + xhr.readyState);
        if (cb && xhr.readyState === xhr.DONE) {
            if (xhr.status >= 200 && xhr.status < 300) {
                console.log("responseText: ", xhr.responseText.toString());
                var res = JSON.parse(xhr.responseText.toString());
                cb(res);
            } else {
                console.log("Status: ", xhr.statusText);
            }
        }
    };

    xhr.ontimeout = function () {
        print("Request timed out");
    };

    xhr.open(verb, BASE + (endpoint || ""));
    xhr.setRequestHeader("Content-Type", "application/json");
    xhr.setRequestHeader("Accept", "application/json");
    data = obj ? JSON.stringify(obj) : "";
    xhr.send(data);
}


function mock_request(verb, endpoint, obj, cb) {
    var mhr = new MockHTTPRequest();

    if (mhr.readyState === mhr.ERROR) {
        // return print("Running standalone: " + mhr.errorString());
        return print("Running standalone");
    }

    mhr.requested.connect(cb);
    mhr.request(verb, BASE + (endpoint || ""), obj);
}


function request(verb, endpoint, obj, cb) {
    if (Model.port === 0) {
        return mock_request(verb, endpoint, obj, cb);
    }

    return real_request(verb, endpoint, obj, cb);
}


function onReady(cb) {
    // Connect and initialise host cb is called upon completion.
    request("POST", "/session", null, cb);

}

function get_instances(cb) {
    request("GET", "/instances", null, cb);
}


function get_plugins(cb) {
    request("GET", "/plugins", null, cb);
}


function get_application(cb) {
    request("GET", "/application", null, cb);
}


function get_processes(cb) {
    request("GET", "/processes", null, cb);
}

function get_process(process_id, cb) {
    request("GET", "/processes/" + process_id, null, cb);
}

function post_processes(instance, plugin, cb) {
    request("POST", "/processes",
            {"instance": instance, "plugin": plugin}, cb);
}