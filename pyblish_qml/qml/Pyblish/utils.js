.pragma library

function toTitleCase(str) {
    return str.replace(/\b\w/g, function (txt) { return txt.toUpperCase(); });
}