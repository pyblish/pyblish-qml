import QtQuick 2.3

Item {
    id: root
 
    // Public API
    property alias font: label.font
    property alias text: label.text
    property variant target: null
    property bool platformInverted: false
 
    opacity: 0
 
    function show() {
        opacity = 1
        visible = true
    }
 
    function hide() {
        opacity = 0
    }
 
    Behavior on opacity {
        PropertyAnimation { duration: 100 }
    }
 
    Component.onCompleted: {
        if (visible)
            show()
    }
 
    onOpacityChanged: {
        if (opacity == 0)
            visible = false
        else
            visible = true
    }
 
    onVisibleChanged: {
        if (visible) {
            root.parent = AppView.visualRoot()
            privy.calculatePosition()
            opacity = 1
            privy.targetSceneXChanged.connect(privy.targetMoved)
            privy.targetSceneYChanged.connect(privy.targetMoved)
        } else {
            privy.targetSceneXChanged.disconnect(privy.targetMoved)
            privy.targetSceneYChanged.disconnect(privy.targetMoved)
        }
    }
 
    Binding { target: privy; property: "targetSceneX"; value: AppView.sceneX(root.target); when: root.visible && (root.target != null) }
    Binding { target: privy; property: "targetSceneY"; value: AppView.sceneY(root.target); when: root.visible && (root.target != null) }
 
    QtObject {
        id: privy
 
        property real hMargin: platformStyle.paddingMedium * 2
        property real vMargin: platformStyle.paddingMedium
        property real spacing: platformStyle.paddingLarge
        property real maxWidth: screen.width - spacing * 2
        property real targetSceneX
        property real targetSceneY
 
        function targetMoved() {
            if (root.opacity == 1)
                hide()
        }
 
        function calculatePosition() {
            if (!target)
                return
 
            // Determine and set the main position for the ToolTip, order: top, right, left, bottom
            var targetPos = root.parent.mapFromItem(target, 0, 0)
 
            // Top
            if (targetPos.y >= (root.height + privy.vMargin + privy.spacing)) {
                root.x = targetPos.x + (target.width / 2) - (root.width / 2)
                root.y = targetPos.y - root.height - privy.vMargin
 
            // Right
            } else if (targetPos.x <= (screen.width - target.width - privy.hMargin - root.width - privy.spacing)) {
                root.x = targetPos.x + target.width + privy.hMargin;
                root.y = targetPos.y + (target.height / 2) - (root.height / 2)
 
            // Left
            } else if (targetPos.x >= (root.width + privy.hMargin + privy.spacing)) {
                root.x = targetPos.x - root.width - privy.hMargin
                root.y = targetPos.y + (target.height / 2) - (root.height / 2)
 
            // Bottom
            } else {
                root.x = targetPos.x + (target.width / 2) - (root.width / 2)
                root.y = targetPos.y + target.height + privy.vMargin
            }
 
            // Fine-tune the ToolTip position based on the screen borders
            if (root.x > (screen.width - privy.spacing - root.width))
                root.x = screen.width - root.width - privy.spacing
 
            if (root.x < privy.spacing)
                root.x = privy.spacing;
 
            if (root.y > (screen.height - root.height - privy.spacing))
                root.y = screen.height - root.height - privy.spacing
 
            if (root.y < privy.spacing)
                root.y = privy.spacing
 
            root.x = Math.round(root.x)
            root.y = Math.round(root.y)
        }
    }
 
    BorderImage {
        id: frame
        anchors.fill: parent
        source: privateStyle.imagePath("qtg_fr_tooltip", root.platformInverted)
        border { left: 20; top: 20; right: 20; bottom: 20 }
    }
 
    Text {
       id: label
       clip: true
       color: root.platformInverted ? platformStyle.colorNormalLightInverted
                                    : platformStyle.colorNormalLight
       elide: Text.ElideRight
       font { family: platformStyle.fontFamilyRegular; pixelSize: platformStyle.fontSizeMedium }
       verticalAlignment: Text.AlignVCenter
       horizontalAlignment: Text.AlignHCenter
       anchors {
           fill: parent
           leftMargin: privy.hMargin
           rightMargin: privy.hMargin
           topMargin: privy.vMargin
           bottomMargin: privy.vMargin
       }
    }
}