pragma ComponentBehavior: Bound
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import QtQuick
import QtQuick.Layouts

/**
 * Collapsible card for a single Uptime Kuma status page.
 */
Rectangle {
    id: root

    required property var page
    required property real contentWidth
    property var store: null
    property bool expanded: true
    property bool restored: false
    property real cardPadding: 6

    readonly property string stateKey: "page:" + (root.page?.slug ?? root.page?.id ?? "")

    function restoreExpansion() {
        root.expanded = root.store ? root.store.get(root.stateKey, true) : true;
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

    readonly property real innerWidth: contentWidth - cardPadding * 2

    implicitWidth: contentWidth
    implicitHeight: column.implicitHeight + cardPadding * 2
    radius: Appearance.rounding.small
    color: Appearance.colors.colLayer2

    StatusColors {
        id: palette
    }

    ColumnLayout {
        id: column
        x: root.cardPadding
        y: root.cardPadding
        width: root.innerWidth
        spacing: 0

        CollapsibleHeader {
            Layout.fillWidth: true
            expanded: root.expanded
            onToggled: root.expanded = !root.expanded

            StatusDot {
                Layout.alignment: Qt.AlignVCenter
                size: 10
                color: palette.forStatus(root.page.status)
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                StyledText {
                    Layout.fillWidth: true
                    text: root.page.title
                    font.pixelSize: Appearance.font.pixelSize.small
                    font.variableAxes: Appearance.font.variableAxes.title
                    color: Appearance.colors.colOnLayer2
                    elide: Text.ElideRight
                }

                StyledText {
                    Layout.fillWidth: true
                    text: palette.labelFor(root.page.status)
                    font.pixelSize: Appearance.font.pixelSize.smallest
                    color: palette.forStatus(root.page.status)
                    elide: Text.ElideRight
                }
            }

            StyledText {
                Layout.alignment: Qt.AlignVCenter
                Layout.preferredWidth: 52
                text: palette.percent(root.page.uptime_24h)
                font.pixelSize: Appearance.font.pixelSize.smaller
                color: Appearance.colors.colOnLayer1Inactive
                horizontalAlignment: Text.AlignRight
            }

            ExpandChevron {
                Layout.alignment: Qt.AlignVCenter
                expanded: root.expanded
            }
        }

        Revealer {
            Layout.fillWidth: true
            vertical: true
            reveal: root.expanded

            ColumnLayout {
                width: root.innerWidth
                spacing: 0

                StyledText {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 4
                    visible: !!root.page.description
                    text: root.page.description ?? ""
                    font.pixelSize: Appearance.font.pixelSize.smallest
                    color: Appearance.colors.colOnLayer1Inactive
                    wrapMode: Text.Wrap
                }

                StyledText {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.rightMargin: 8
                    Layout.bottomMargin: 4
                    visible: !!root.page.error
                    text: root.page.error ?? ""
                    font.pixelSize: Appearance.font.pixelSize.smallest
                    color: Appearance.colors.colError
                    wrapMode: Text.Wrap
                }

                StyledText {
                    Layout.fillWidth: true
                    Layout.leftMargin: 8
                    Layout.bottomMargin: 4
                    visible: !root.page.error && root.page.groups.length === 0
                    text: Translation.tr("This status page has no monitors.")
                    font.pixelSize: Appearance.font.pixelSize.smallest
                    color: Appearance.colors.colOnLayer1Inactive
                }

                Repeater {
                    model: root.page.groups

                    delegate: MonitorGroup {
                        required property var modelData
                        Layout.fillWidth: true
                        group: modelData
                        contentWidth: root.innerWidth
                        store: root.store
                        parentKey: root.stateKey
                    }
                }
            }
        }
    }
}
