import QtQuick 2.3

import "../generic" as Generic
import "../service/constant.js" as Constant
import "../list" as Superclass
import "controller.js" as Ctrl

Superclass.Item {
    id: root
    signal validate(string family)

    onValidate: Ctrl.validate(family)
}
