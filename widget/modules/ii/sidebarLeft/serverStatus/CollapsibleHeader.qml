import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

/**
 * Clickable header that toggles a collapsible section.
 */
Rectangle {
    id: root

    property bool expanded: false
    property real horizontalPadding: 8
    property real verticalPadding: 6
    default property alias content: contentRow.data

    signal toggled

    implicitHeight: contentRow.implicitHeight + verticalPadding * 2
    radius: Appearance.rounding.small
    color: hoverArea.containsMouse ? Appearance.colors.colLayer2Hover : "transparent"

    Behavior on color {
        animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
    }

    RowLayout {
        id: contentRow
        anchors {
            fill: parent
            leftMargin: root.horizontalPadding
            rightMargin: root.horizontalPadding
        }
        spacing: 8
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: root.toggled()
    }
}
