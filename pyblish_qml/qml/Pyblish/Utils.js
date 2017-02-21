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

function showContextMenu(parent, children, x, y) {
  var root = findRoot(parent);
  var component = Qt.createComponent("contextMenu.qml")
  var x, y;

  var menu = component.createObject(root, {
    "children": children,
    "menuX": x,
    "menuY": y,
    "z": 4,
  })

  if (menu === null)
    console.error("Error creating menu: " + component.errorString())
  else
    menu.show()


  return menu
}

