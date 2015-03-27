.pragma library

function toTitleCase(str) {
    return str.replace(/\b\w/g, function (txt) { return txt.toUpperCase(); });
}

function findRoot(obj) {
    while (obj.parent) {
        obj = obj.parent
    }

    return obj
}