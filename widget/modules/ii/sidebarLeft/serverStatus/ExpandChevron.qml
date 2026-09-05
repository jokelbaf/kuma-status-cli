import qs.modules.common
import qs.modules.common.widgets
import QtQuick

/**
 * Chevron that points down when collapsed and up when expanded.
 */
MaterialSymbol {
    id: root

    property bool expanded: false

    text: "keyboard_arrow_down"
    iconSize: Appearance.font.pixelSize.large
    color: Appearance.colors.colOnLayer1Inactive
    rotation: expanded ? 180 : 0

    Behavior on rotation {
        animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
    }
}
