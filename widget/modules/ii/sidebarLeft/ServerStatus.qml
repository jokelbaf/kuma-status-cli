pragma ComponentBehavior: Bound
import qs.services
import qs.modules.common
import qs.modules.common.widgets
import qs.modules.ii.sidebarLeft.serverStatus
import QtQuick
import QtQuick.Layouts
import Quickshell
import Quickshell.Io

/**
 * Uptime Kuma status pages, read through the `kuma-status-cli` command.
 */
Item {
    id: root

    property real padding: 10
    property var snapshot: null
    property string errorText: ""
    property bool loading: false
    property bool receivedOutput: false
    property int lastExitCode: 0
    property date lastUpdated: new Date(0)

    property var options: Config.options.sidebar.serverStatus
    readonly property var pages: root.snapshot?.pages ?? []
    readonly property string overallStatus: root.snapshot?.status ?? "unknown"
    readonly property real contentWidth: root.width - root.padding * 2

    function refresh() {
        if (root.loading)
            return;
        root.loading = true;
        root.receivedOutput = false;
        root.lastExitCode = 0;
        fetchProc.running = true;
    }

    function applyOutput(text) {
        root.receivedOutput = true;
        if (!text || text.trim().length === 0) {
            root.errorText = Translation.tr("The status command returned nothing.");
            return;
        }
        try {
            const data = JSON.parse(text);
            if (data.error) {
                root.errorText = data.error;
                return;
            }
            root.snapshot = data;
            root.errorText = "";
            root.lastUpdated = new Date();
        } catch (parseError) {
            root.errorText = Translation.tr("Could not parse the status output: %1").arg(parseError);
        }
    }

    function summaryText() {
        if (!root.snapshot)
            return "";
        const counts = root.snapshot.monitor_counts;
        const parts = ["up", "down", "pending", "maintenance", "paused"]
            .filter(state => counts[state] > 0)
            .map(state => `${counts[state]} ${palette.stateLabelFor(state).toLowerCase()}`);
        if (root.snapshot.uptime_24h !== null)
            parts.push(Translation.tr("%1 avg 24h").arg(palette.percent(root.snapshot.uptime_24h)));
        return parts.join("  -  ");
    }

    onVisibleChanged: {
        if (visible && !root.snapshot)
            root.refresh();
    }

    Component.onCompleted: root.refresh()

    StatusColors {
        id: palette
    }

    Process {
        id: fetchProc
        command: root.options.command.concat(["--json", "--beats", String(root.options.beats)])

        stdout: StdioCollector {
            onStreamFinished: root.applyOutput(this.text)
        }

        onExited: (exitCode, exitStatus) => root.lastExitCode = exitCode

        onRunningChanged: {
            if (fetchProc.running)
                return;
            root.loading = false;
            Qt.callLater(() => {
                if (root.receivedOutput)
                    return;
                root.errorText = root.lastExitCode === 0
                    ? Translation.tr("Could not run %1.").arg(root.options.command.join(" "))
                    : Translation.tr("%1 exited with code %2.").arg(root.options.command.join(" ")).arg(root.lastExitCode);
            });
        }
    }

    Timer {
        id: watchdog
        interval: 30000
        running: root.loading
        onTriggered: {
            fetchProc.running = false;
            root.loading = false;
            if (!root.receivedOutput)
                root.errorText = Translation.tr("The status command timed out.");
        }
    }

    Timer {
        interval: root.options.interval
        running: root.options.interval > 0
        repeat: true
        onTriggered: root.refresh()
    }

    ColumnLayout {
        anchors {
            fill: parent
            margins: root.padding
        }
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 8

            MaterialSymbol {
                text: "dns"
                iconSize: Appearance.font.pixelSize.huge
                color: Appearance.colors.colOnLayer1
            }

            ColumnLayout {
                Layout.fillWidth: true
                spacing: 0

                StyledText {
                    Layout.fillWidth: true
                    text: Translation.tr("Server status")
                    font.pixelSize: Appearance.font.pixelSize.normal
                    font.variableAxes: Appearance.font.variableAxes.title
                    color: Appearance.colors.colOnLayer1
                    elide: Text.ElideRight
                }

                StyledText {
                    Layout.fillWidth: true
                    visible: !!root.snapshot
                    text: root.snapshot ? `${root.snapshot.url}${root.snapshot.version ? "  -  v" + root.snapshot.version : ""}` : ""
                    font.pixelSize: Appearance.font.pixelSize.smallest
                    color: Appearance.colors.colOnLayer1Inactive
                    elide: Text.ElideRight
                }
            }

            RippleButton {
                implicitWidth: 34
                implicitHeight: 34
                buttonRadius: Appearance.rounding.full
                onClicked: root.refresh()

                contentItem: MaterialSymbol {
                    anchors.centerIn: parent
                    text: "refresh"
                    iconSize: Appearance.font.pixelSize.larger
                    color: Appearance.colors.colOnLayer1

                    RotationAnimation on rotation {
                        running: root.loading
                        alwaysRunToEnd: true
                        loops: Animation.Infinite
                        from: 0
                        to: 360
                        duration: 1200
                    }
                }

                StyledToolTip {
                    text: Translation.tr("Refresh")
                }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            visible: !!root.snapshot
            implicitHeight: bannerRow.implicitHeight + 20
            radius: Appearance.rounding.normal
            color: palette.containerFor(root.overallStatus)

            Behavior on color {
                animation: Appearance.animation.elementMoveFast.colorAnimation.createObject(this)
            }

            RowLayout {
                id: bannerRow
                anchors {
                    fill: parent
                    leftMargin: 12
                    rightMargin: 12
                }
                spacing: 10

                StatusDot {
                    Layout.alignment: Qt.AlignVCenter
                    size: 12
                    color: palette.forStatus(root.overallStatus)
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 1

                    StyledText {
                        Layout.fillWidth: true
                        text: palette.labelFor(root.overallStatus)
                        font.pixelSize: Appearance.font.pixelSize.small
                        font.variableAxes: Appearance.font.variableAxes.title
                        color: palette.forStatus(root.overallStatus)
                        elide: Text.ElideRight
                    }

                    StyledText {
                        Layout.fillWidth: true
                        text: root.summaryText()
                        font.pixelSize: Appearance.font.pixelSize.smallest
                        color: Appearance.colors.colOnLayer2
                        elide: Text.ElideRight
                    }
                }
            }
        }

        Item {
            Layout.fillWidth: true
            Layout.fillHeight: true

            StyledFlickable {
                id: flickable
                anchors.fill: parent
                visible: root.pages.length > 0
                contentWidth: width
                contentHeight: pageColumn.implicitHeight
                clip: true

                ColumnLayout {
                    id: pageColumn
                    width: flickable.width
                    spacing: 8

                    Repeater {
                        model: root.pages

                        delegate: StatusPageCard {
                            required property var modelData
                            Layout.fillWidth: true
                            page: modelData
                            contentWidth: flickable.width
                        }
                    }
                }
            }

            PagePlaceholder {
                shown: root.pages.length === 0
                icon: root.errorText.length > 0 ? "cloud_off" : "dns"
                title: root.loading ? Translation.tr("Loading...")
                    : (root.errorText.length > 0 ? Translation.tr("Unavailable") : Translation.tr("No status pages"))
                description: root.loading ? Translation.tr("Reading status pages from Uptime Kuma.")
                    : (root.errorText.length > 0 ? root.errorText
                    : Translation.tr("Run `kuma-status-cli configure` to connect an Uptime Kuma instance."))
                descriptionHorizontalAlignment: Text.AlignHCenter
            }
        }

        StyledText {
            Layout.fillWidth: true
            visible: root.lastUpdated.getTime() > 0
            text: Translation.tr("Updated %1").arg(Qt.formatDateTime(root.lastUpdated, "hh:mm:ss"))
                + (root.errorText.length > 0 ? `  -  ${root.errorText}` : "")
            font.pixelSize: Appearance.font.pixelSize.smallest
            color: root.errorText.length > 0 ? Appearance.colors.colError : Appearance.colors.colOnLayer1Inactive
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
        }
    }
}
