pragma ComponentBehavior: Bound
import qs.modules.common
import qs.modules.common.widgets
import QtQuick

/**
 * Row of rounded heartbeat bumps, newest on the right, like an Uptime Kuma status page.
 */
Item {
    id: root

    property var beats: []
    property bool muted: false
    property real beatWidth: 5
    property real beatSpacing: 2
    property real beatHeight: 18

    readonly property real beatStride: beatWidth + beatSpacing
    readonly property int capacity: Math.max(1, Math.floor((width + beatSpacing) / beatStride))
    readonly property var visibleBeats: root.beats.slice(Math.max(0, root.beats.length - root.capacity))
    readonly property real rowWidth: Math.max(0, root.visibleBeats.length * root.beatStride - root.beatSpacing)

    implicitWidth: 60
    implicitHeight: beatHeight
    clip: true

    StatusColors {
        id: palette
    }

    Row {
        id: beatRow
        anchors {
            right: parent.right
            verticalCenter: parent.verticalCenter
        }
        spacing: root.beatSpacing

        Repeater {
            model: root.visibleBeats

            delegate: Rectangle {
                id: bump
                required property int index
                required property var modelData

                width: root.beatWidth
                height: root.beatHeight
                radius: root.beatWidth / 2
                color: root.muted ? palette.colIdle : palette.forState(bump.modelData.status)
                opacity: hoverArea.hoveredIndex < 0 || hoverArea.hoveredIndex === bump.index ? 1 : 0.55

                Behavior on opacity {
                    animation: Appearance.animation.elementMoveFast.numberAnimation.createObject(this)
                }
            }
        }
    }

    MouseArea {
        id: hoverArea
        anchors.fill: parent
        hoverEnabled: true
        acceptedButtons: Qt.NoButton

        property int hoveredIndex: -1
        readonly property var hoveredBeat: hoveredIndex >= 0 ? root.visibleBeats[hoveredIndex] : null

        onPositionChanged: mouse => {
            const offset = mouse.x - beatRow.x;
            const index = Math.floor(offset / root.beatStride);
            hoveredIndex = (offset < 0 || index >= root.visibleBeats.length) ? -1 : index;
        }
        onExited: hoveredIndex = -1

        StyledToolTip {
            extraVisibleCondition: hoverArea.containsMouse && hoverArea.hoveredBeat !== null
            text: hoverArea.hoveredBeat === null ? "" :
                `${palette.stateLabelFor(hoverArea.hoveredBeat.status)}  -  ${palette.ping(hoverArea.hoveredBeat.ping)}`
                + (hoverArea.hoveredBeat.time ? `\n${hoverArea.hoveredBeat.time}` : "")
                + (hoverArea.hoveredBeat.message ? `\n${hoverArea.hoveredBeat.message}` : "")
        }
    }
}
