.pragma library

var components = {
    "context":    Qt.createComponent("delegates/ContextDelegate.qml"),
    "error":      Qt.createComponent("delegates/ErrorDelegate.qml"),
    "instance":   Qt.createComponent("delegates/InstanceDelegate.qml"),
    "message":    Qt.createComponent("delegates/MessageDelegate.qml"),
    "plugin":     Qt.createComponent("delegates/PluginDelegate.qml"),
    "record":     Qt.createComponent("delegates/RecordDelegate.qml"),
    "gadget":     Qt.createComponent("delegates/GadgetDelegate.qml"),
}
