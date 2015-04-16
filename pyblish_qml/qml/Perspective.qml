// import QtQuick 2.3
// import QtGraphicalEffects 1.0
// import Pyblish 0.1
// import "Delegates.js" as Delegates
// import Perspective 0.1 as Perspective


// Item {
//     id: root

//     Column {
//         anchors.fill: parent

//         ActionBar {
//             id: actionBar

//             width: parent.width
//             height: 50

//             actions: [
//                 Action {
//                     iconName: "button-back"
//                     onTriggered: stack.pop()
//                 }
//             ]

//             elevation: 1
//         }

//         View {
//             elevation: 1
//             width: parent.width
//             height: root.height - actionBar.height

//             View {
//                 anchors.fill: parent
//                 anchors.margins: 8
//                 elevation: -1

//                 ListView {
//                     id: body

//                     anchors.top: dropShadowContainer.bottom
//                     anchors.bottom: parent.bottom

//                     interactive: false

//                     anchors.left: parent.left
//                     anchors.right: parent.right
//                     anchors.margins: 10

//                     boundsBehavior: Flickable.StopAtBounds

//                     spacing: -1

//                     model: [
//                         {
//                             "type": "documentation",
//                             "name": "Documentation",
//                             "tab": true,
//                             "closed": true,
//                             "gutter": false,
//                             "model": app.gadgetProxy
//                         },
//                         {
//                             "type": "errors",
//                             "name": "Errors",
//                             "tab": true,
//                             "closed": false,
//                             "model": app.errorProxy
//                         },
//                         {
//                             "type": "records",
//                             "name": "Records",
//                             "tab": true,
//                             "closed": false,
//                             "model": app.recordProxy
//                         },
//                         // {
//                         //     "type": "plugins",
//                         //     "name": "Plug-ins",
//                         //     "tab": true,
//                         //     "closed": false,
//                         //     "model": app.pluginProxy
//                         // },
//                         // {
//                         //     "type": "instances",
//                         //     "name": "Instances",
//                         //     "tab": true,
//                         //     "closed": false,
//                         //     "model": app.instanceProxy
//                         // },
//                     ]

//                     delegate: Loader {
//                         width: ListView.view.width
//                         sourceComponent: Delegates.components[modelData.type]
//                     }
//                 }

//                 Item {
//                     id: dropShadowContainer

//                     visible: false

//                     anchors.top: parent.top
//                     anchors.left: parent.left
//                     anchors.right: parent.right
//                     anchors.margins: {
//                         leftMargin: 2
//                         rightMargin: 2
//                         topMargin: 2
//                     }

//                     height: 180

//                     Perspective.Header {
//                         id: header
//                         anchors.fill: parent
//                     }
//                 }

//                 DropShadow {
//                     source: dropShadowContainer
//                     anchors.fill: source
//                     verticalOffset: 3
//                     radius: 8.0
//                     samples: 16
//                     fast: true
//                     color: "#80000000"
//                 }
//             }
//         }
//     }
// }