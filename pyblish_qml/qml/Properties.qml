import QtQuick 2.3
import Pyblish 0.1
import QtWebKit 3.0


Item {
    id: properties

    property string type
    property int currentIndex

    property var itemData: {}

    View {
        id: header

        height: 50

        anchors.left: parent.left
        anchors.right: parent.right

        elevation: 1

        Row {

            anchors.fill: parent
            anchors.margins: header.margins

            Button {
                id: back

                icon: "button-back"
                
                anchors.verticalCenter: parent.verticalCenter

                onClicked: stack.pop()
            }

            Button {                
                anchors.verticalCenter: parent.verticalCenter

                text: "Home"

                onClicked: stack.pop()
            }

            Label {                
                style: "title"
                
                text: "/"

                anchors.verticalCenter: parent.verticalCenter
            }

            Button {
                text: "Properties"

                anchors.verticalCenter: parent.verticalCenter
            }
        }
    }

    View {
        id: body

        elevation: -1

        anchors.top: header.bottom

        width: parent.width
        height: parent.height - header.height

        Column {
            id: bodyColumn

            spacing: 5
            
            anchors.fill: parent
            anchors.margins: 10

            Label {
                id: headline

                style: "headline"

                text: itemData.name
            }

            TextArea {
                id: description

                width: bodyColumn.width
                
                text: itemData.doc != null ? itemData.doc : ""
            }

            Repeater {
                id: repeater

                model: {
                    var data = []

                    if (typeof itemData.data != "undefined") {
                    
                        Object.keys(itemData.data).forEach(function (key) {
                            data.push({"key": key,
                                       "value": itemData.data[key]})
                        })
                    }

                    return data
                }

                delegate: Row {

                    spacing: 3

                    Label {
                        text: modelData.key
                    }

                    Label {
                        text: "="
                    }

                    Label {
                        text: modelData.value
                    }

                }
            }
        }
    }
}
