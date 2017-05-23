import QtQuick 2.6
import QtQuick.Layouts 1.1

import Pyblish 0.1

Rectangle {
    id: root
    clip: true
    height: 0

    color: Theme.backgroundColor

    property bool isUp
    property bool isMaximised

    property alias summary: commentSummary.text
    property alias description: commentDescription.text

    property var readOnly: false

    Behavior on height {
        NumberAnimation {
            duration: 500
            easing.type: Easing.OutQuint
        }
    }

    function up() {
        isUp = true
        commentSummary.forceActiveFocus()
    }

    function down() {
        isUp = false
        isMaximised = false
    }

    function toggle() {
        isUp ? down() : up()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 5

        View {
            radius: 3
            height: 27
            elevation: -1
            Layout.fillWidth: true

            RowLayout {
                anchors.fill: parent
                anchors.margins: 5
                
                TextInput {
                    id: commentSummary
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    color: "white"
                    selectionColor: "#222"
                    readOnly: root.readOnly
                    selectByMouse: true
                    clip: true

                    font.family: "Open Sans"
                    font.weight: Font.Normal

                    KeyNavigation.tab: commentDescription
                    KeyNavigation.backtab: commentDescription
                    KeyNavigation.priority: KeyNavigation.BeforeItem

                    Label {
                        text: "Summary"
                        opacity: 0.5
                        visible: parent.length == 0
                    }

                    onTextChanged: app.commenting(
                        commentSummary.text,
                        commentDescription.text
                    );
                }

                AwesomeButton {
                    name: "arrows-alt"
                    Layout.fillHeight: true
                    onClicked: root.isMaximised = root.isMaximised ? false : true
                }
            }

        }

        View {
            radius: 3
            elevation: -1
            Layout.fillHeight: true
            Layout.fillWidth: true

            TextEdit {
                id: commentDescription
                anchors.fill: parent
                anchors.margins: 5
                color: "white"
                selectionColor: "#222"
                selectByMouse: true
                readOnly: root.readOnly
                wrapMode: TextEdit.WordWrap
                clip: true

                Label {
                    text: "Description"
                    opacity: 0.5
                    visible: parent.length == 0
                }

                font.family: "Open Sans"
                font.weight: Font.Normal

                KeyNavigation.backtab: commentSummary
                KeyNavigation.priority: KeyNavigation.BeforeItem

                onTextChanged: app.commenting(
                    commentSummary.text,
                    commentDescription.text
                );
            }
        }
    }
}
