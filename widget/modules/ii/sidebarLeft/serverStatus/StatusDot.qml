import qs.modules.common
import QtQuick

/**
 * Small filled circle indicating a monitor state or an aggregated status.
 */
Rectangle {
    id: root

    property real size: 8

    implicitWidth: size
    implicitHeight: size
    radius: size / 2

    Behavior on color {
        animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
    }
}
