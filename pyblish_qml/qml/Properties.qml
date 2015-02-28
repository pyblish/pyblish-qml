import QtQuick 2.3
import Pyblish 0.1


Flickable {
    id: properties

    contentHeight: content.height
    boundsBehavior: Flickable.DragOverBounds

    property var itemData: {}

    property var model: {
        var sourceData,
            data = []

        if (typeof itemData.data == "undefined")
            var sourceData = itemData
        else
            var sourceData = itemData.data
        
        Object.keys(sourceData).forEach(function (key) {
            data.push({"value": key, "column": 0})
            data.push({"value": sourceData[key], "column": 1})
        })

        return data
    }

    Column {
        id: content

        ActionBar {
            id: header

            actions: [
                Action {
                    iconName: "button-back"
                    onTriggered: stack.pop()
                },

                Action {
                    name: itemData.name
                }
            ]

            width: properties.width

            elevation: 1
        }

        View {
            id: body

            elevation: -1

            width: properties.width
            height: 400

            Column {
                id: bodyColumn

                spacing: 5
                
                anchors.fill: parent
                anchors.margins: 10

                View {
                    height: 50
                    width: bodyColumn.width

                    elevation: -1

                    Label {
                        id: headline

                        anchors.fill: parent
                        anchors.margins: parent.margins

                        style: "headline"

                        text: itemData.name
                    }
                }


                View {
                    height: 100
                    width: bodyColumn.width

                    elevation: -1

                    TextArea {
                        id: description

                        anchors.fill: parent
                        anchors.margins: parent.margins
                        
                        text: itemData.doc != null ? itemData.doc : "No description"
                    }
                }

                View {
                    height: bodyColumn.height - 150 - margins * 2
                    width: bodyColumn.width

                    elevation: 1

                    Grid {
                        columns: 2
                        columnSpacing: 10

                        anchors.fill: parent
                        anchors.margins: parent.margins

                        Repeater {
                            id: repeater

                            delegate: property

                            model: properties.model
                        }
                    }
                }
            }
        }
    }

    Component {
        id: property

        Loader {
            id: loader

            property var value: modelData.value

            visible: loader.status == Loader.Ready

            Component.onCompleted: {
                if (modelData.column == 0) {
                    loader.sourceComponent = labelProperty

                } else if (typeof value == "number") {
                    loader.sourceComponent = numberProperty

                } else {
                    loader.sourceComponent = textProperty
                }
            }
        }
    }

    Component {
        id: labelProperty

        Label {
            id: label

            font.weight: Font.DemiBold

            text: value
        }
    }

    Component {
        id: textProperty

        TextField {
            id: label

            anchors.verticalCenter: parent.verticalCenter
            
            text: JSON.stringify(value)
        }
    }

    Component {
        id: numberProperty

        View {
            width: label.paintedWidth + 48

            SpinBox {
                id: label
                anchors.fill: parent
                anchors.margins: parent.margins
                anchors.verticalCenter: parent.verticalCenter
                value: value
            }
        }
    }
}
