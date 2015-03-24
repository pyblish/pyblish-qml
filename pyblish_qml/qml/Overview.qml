import QtQuick 2.3
import Pyblish 0.1


Item {
    id: overview

    property string __lastPlugin

    signal instanceDoubleClicked(int index)
    signal pluginDoubleClicked(int index)

    states: [
        State {
            name: "publishing"
        },

        State {
            name: "finished"
        }
    ]

    function setMessage(message) {
        footer.message.text = message
        footer.message.animation.restart()
        footer.message.animation.start()
        app.log.info(message)
    }

    TabBar {
        id: tabBar

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        tabs: [
            {
                text: "",
                icon: "logo-white"
            },
            "Terminal"
        ]
    }

    View {
        id: tabView

        anchors.top: tabBar.bottom
        anchors.bottom: footer.top
        anchors.horizontalCenter: parent.horizontalCenter
        anchors.margins: tabView.margins
        anchors.bottomMargin: 0

        width: parent.width - 10

        elevation: -1

        Row {
            visible: tabBar.currentIndex == 0

            anchors.fill: parent
            anchors.margins: parent.margins

            List {
                model: app.instanceProxy
                width: parent.width / 2
                height: parent.height

                section.property: "family"

                onItemClicked: app.toggleInstance(index)
                onItemDoubleClicked: overview.instanceDoubleClicked(index)
            }

            List {
                model: app.pluginProxy
                width: parent.width / 2
                height: parent.height

                section.property: "type"

                onItemClicked: app.togglePlugin(index)
                onItemDoubleClicked: overview.pluginDoubleClicked(index)
            }
        }

        Terminal {
            id: terminal
            anchors.fill: parent
            anchors.margins: parent.margins
            
            visible: tabBar.currentIndex == 1
        }
    }


    Footer {
        id: footer

        mode: overview.state == "publishing" ? 1 : overview.state == "finished" ? 2 : 0

        width: parent.width
        anchors.bottom: parent.bottom

        onPublish: {
            overview.state = "publishing"
            app.start()
        }

        onReset: {
            overview.state = ""
            setMessage("Resetting..")
            app.reset()
        }

        onStop: {
            overview.state = "finished"
            setMessage("Stopping..")
            app.stop()
        }

        onSave: {
            app.save()
        }
    }

    Connections {
        target: app

        /*
         * Print results of publish in Terminal
        */
        onProcessed: {
        }

        onFinished: {
            overview.state = "finished"
            setMessage("Finished")
        }

        onError: {
            setMessage(message)
        }

        onInfo: {
        }

        onSaved: {
            setMessage("Saved")
        }
    }
}