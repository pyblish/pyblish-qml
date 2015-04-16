.pragma library

/*
 * Pre-load delegates
 *
 *
*/
var components = {
    "context":       Qt.createComponent("delegates/ContextDelegate.qml"),
    "error":         Qt.createComponent("delegates/ErrorDelegate.qml"),
    "errors":        Qt.createComponent("delegates/ErrorsDelegate.qml"),
    "instance":      Qt.createComponent("delegates/InstanceDelegate.qml"),
    "message":       Qt.createComponent("delegates/MessageDelegate.qml"),
    "plugin":        Qt.createComponent("delegates/PluginDelegate.qml"),
    "record":        Qt.createComponent("delegates/RecordDelegate.qml"),
    "records":       Qt.createComponent("delegates/RecordsDelegate.qml"),
    "gadget":        Qt.createComponent("delegates/GadgetDelegate.qml"),
    "documentation": Qt.createComponent("delegates/DocumentationDelegate.qml"),
    "spacer":        Qt.createComponent("delegates/SpacerDelegate.qml"),
}
