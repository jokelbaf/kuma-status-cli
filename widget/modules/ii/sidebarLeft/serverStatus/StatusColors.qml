import qs.services
import qs.modules.common
import qs.modules.common.functions
import QtQuick

/**
 * Maps Uptime Kuma monitor states and aggregated statuses to Material colors.
 */
QtObject {
    id: root

    readonly property color colUp: Appearance.m3colors.m3success
    readonly property color colDown: Appearance.colors.colError
    readonly property color colPending: "#F2B33D"
    readonly property color colMaintenance: Appearance.colors.colPrimary
    readonly property color colIdle: Appearance.colors.colOutlineVariant

    function forState(state) {
        switch (state) {
        case "up": return root.colUp;
        case "down": return root.colDown;
        case "pending": return root.colPending;
        case "maintenance": return root.colMaintenance;
        default: return root.colIdle;
        }
    }

    function forStatus(status) {
        switch (status) {
        case "operational": return root.colUp;
        case "degraded": return root.colPending;
        case "outage": return root.colDown;
        case "maintenance": return root.colMaintenance;
        default: return root.colIdle;
        }
    }

    function containerFor(status) {
        return ColorUtils.mix(root.forStatus(status), Appearance.colors.colLayer2, 0.15);
    }

    function labelFor(status) {
        switch (status) {
        case "operational": return Translation.tr("All systems operational");
        case "degraded": return Translation.tr("Partially degraded service");
        case "outage": return Translation.tr("Major outage");
        case "maintenance": return Translation.tr("Under maintenance");
        case "paused": return Translation.tr("All monitors paused");
        default: return Translation.tr("No data");
        }
    }

    function stateLabelFor(state) {
        switch (state) {
        case "up": return Translation.tr("Up");
        case "down": return Translation.tr("Down");
        case "pending": return Translation.tr("Pending");
        case "maintenance": return Translation.tr("Maintenance");
        case "paused": return Translation.tr("Paused");
        default: return Translation.tr("Unknown");
        }
    }

    function percent(value) {
        return value === null || value === undefined ? "-" : `${value.toFixed(2)}%`;
    }

    function ping(value) {
        return value === null || value === undefined ? "-" : `${Math.round(value)} ms`;
    }
}
