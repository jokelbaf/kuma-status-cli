pragma ComponentBehavior: Bound
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

/**
 * One monitor with its heartbeat bar and an expandable detail panel.
 */
Item {
    id: root

    required property var monitor
    required property real contentWidth
    property var store: null
    property string parentKey: ""
    property bool expanded: false
    property bool restored: false

    readonly property string stateKey: root.parentKey + "/monitor:" + (root.monitor?.id ?? root.monitor?.name ?? "")

    function restoreExpansion() {
        root.expanded = root.store ? root.store.get(root.stateKey, false) : false;
    }

    Component.onCompleted: {
        root.restoreExpansion();
        root.restored = true;
    }

    onStateKeyChanged: {
        if (root.restored)
            root.restoreExpansion();
    }

    onExpandedChanged: {
        if (root.restored && root.store)
            root.store.set(root.stateKey, root.expanded);
    }

    readonly property var lastBeat: monitor.heartbeats.length > 0 ? monitor.heartbeats[monitor.heartbeats.length - 1] : null
    readonly property var details: [
        { "label": Translation.tr("State"), "value": palette.stateLabelFor(root.monitor.status) },
        { "label": Translation.tr("Type"), "value": root.monitor.type },
        { "label": Translation.tr("Ping"), "value": palette.ping(root.monitor.ping) },
        { "label": Translation.tr("Average ping"), "value": palette.ping(root.monitor.avg_ping) },
        { "label": Translation.tr("Uptime 24h"), "value": palette.percent(root.monitor.uptime_24h) },
        { "label": Translation.tr("Uptime 30d"), "value": palette.percent(root.monitor.uptime_30d) },
    ].concat(
        root.monitor.url ? [{ "label": Translation.tr("URL"), "value": root.monitor.url }] : [],
        root.lastBeat && root.lastBeat.time ? [{ "label": Translation.tr("Last check"), "value": root.lastBeat.time }] : [],
        root.monitor.message ? [{ "label": Translation.tr("Message"), "value": root.monitor.message }] : []
    )

    implicitWidth: contentWidth
    implicitHeight: column.implicitHeight

    StatusColors {
        id: palette
    }

    ColumnLayout {
        id: column
        width: root.contentWidth
        spacing: 0

        CollapsibleHeader {
            Layout.fillWidth: true
            expanded: root.expanded
            horizontalPadding: 6
            verticalPadding: 4
            onToggled: root.expanded = !root.expanded

            StatusDot {
                Layout.alignment: Qt.AlignVCenter
                size: 8
                color: palette.forState(root.monitor.status)
            }

            StyledText {
                Layout.preferredWidth: Math.max(56, root.contentWidth * 0.36)
                Layout.maximumWidth: Layout.preferredWidth
                text: root.monitor.name
                font.pixelSize: Appearance.font.pixelSize.smaller
                color: root.monitor.status === "paused" ? Appearance.colors.colOnLayer1Inactive : Appearance.colors.colOnLayer2
                elide: Text.ElideRight
            }

            HeartbeatBar {
                Layout.fillWidth: true
                Layout.minimumWidth: 40
                Layout.alignment: Qt.AlignVCenter
                beats: root.monitor.heartbeats
                muted: root.monitor.status === "paused"
            }

            StyledText {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 44
                text: palette.percent(root.monitor.uptime_24h)
                font.pixelSize: Appearance.font.pixelSize.smallest
                color: Appearance.colors.colOnLayer1Inactive
                horizontalAlignment: Text.AlignRight
            }

            ExpandChevron {
                Layout.alignment: Qt.AlignVCenter
                expanded: root.expanded
                iconSize: Appearance.font.pixelSize.normal
            }
        }

        Revealer {
            Layout.fillWidth: true
            vertical: true
            reveal: root.expanded

            ColumnLayout {
                width: root.contentWidth
                spacing: 2

                Item {
                    Layout.preferredHeight: 2
                }

                Repeater {
                    model: root.details

                    delegate: DetailRow {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.leftMargin: 20
                        Layout.rightMargin: 6
                        label: modelData.label
                        value: modelData.value
                    }
                }

                Item {
                    Layout.preferredHeight: 6
                }
            }
        }
    }
}
