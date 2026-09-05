pragma ComponentBehavior: Bound
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

/**
 * Collapsible group of monitors inside a status page.
 */
Item {
    id: root

    required property var group
    required property real contentWidth
    property bool expanded: true

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
                size: 6
                color: palette.forStatus(root.group.status)
            }

            StyledText {
                Layout.fillWidth: true
                text: root.group.name
                font.pixelSize: Appearance.font.pixelSize.smaller
                font.variableAxes: Appearance.font.variableAxes.title
                color: Appearance.colors.colOnLayer2
                elide: Text.ElideRight
            }

            StyledText {
                Layout.alignment: Qt.AlignVCenter
                text: root.group.monitors.length === 1 ? Translation.tr("1 monitor")
                    : Translation.tr("%1 monitors").arg(root.group.monitors.length)
                font.pixelSize: Appearance.font.pixelSize.smallest
                color: Appearance.colors.colOnLayer1Inactive
            }

            StyledText {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 44
                text: palette.percent(root.group.uptime_24h)
                font.pixelSize: Appearance.font.pixelSize.smallest
                color: palette.forStatus(root.group.status)
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
                spacing: 0

                Repeater {
                    model: root.group.monitors

                    delegate: MonitorRow {
                        required property var modelData
                        Layout.fillWidth: true
                        Layout.leftMargin: 10
                        monitor: modelData
                        contentWidth: root.contentWidth - 10
                    }
                }
            }
        }
    }
}
