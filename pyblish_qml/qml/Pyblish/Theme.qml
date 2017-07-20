import QtQuick 2.0

pragma Singleton


Object {
    id: theme

    property color primaryColor: "#99CEEE"
    property color primaryDarkColor: "#1976D2"
    property color accentColor: "#99CEEE"
    property color backgroundColor: Qt.rgba(0.3, 0.3, 0.3)
    property ThemePalette light: ThemePalette { light: true }
    property ThemePalette dark: ThemePalette { light: false }

    /*!
       A utility method for changing the alpha on colors. Returns a new object, and does not modify
       the original color at all.
     */
    function alpha(color, alpha) {
        // Make sure we have a real color object to work with (versus a string like "#ccc")
        var realColor = Qt.darker(color, 1)

        realColor.a = alpha

        return realColor
    }

    /*!
       Select a color depending on whether the background is light or dark.

       \c lightColor is the color used on a light background.

       \c darkColor is the color used on a dark background.
     */
    function lightDark(background, lightColor, darkColor) {
        var temp = Qt.darker(background, 1)

        var a = 1 - ( 0.299 * temp.r + 0.587 * temp.g + 0.114 * temp.b);

        if (temp.a === 0 || a < 0.3)
            return lightColor
        else
            return darkColor
    }

    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-Bold.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-BoldItalic.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-ExtraBold.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-ExtraBoldItalic.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-Italic.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-Light.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-LightItalic.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-Regular.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-Semibold.ttf")}
    FontLoader {source: Qt.resolvedUrl("fonts/opensans/OpenSans-SemiboldItalic.ttf")}
}