import QtQuick 2.3
import "feature/service/constant.js" as Constants

Rectangle {
    Component.onCompleted: {
        print(Constants);
    }
}