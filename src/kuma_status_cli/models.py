"""Data model describing an Uptime Kuma status snapshot."""

import dataclasses
import enum


class MonitorState(enum.StrEnum):
    """State of a single monitor."""

    UP = "up"
    DOWN = "down"
    PENDING = "pending"
    MAINTENANCE = "maintenance"
    PAUSED = "paused"
    UNKNOWN = "unknown"


class OverallStatus(enum.StrEnum):
    """Aggregated state of a collection of monitors."""

    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OUTAGE = "outage"
    MAINTENANCE = "maintenance"
    PAUSED = "paused"
    UNKNOWN = "unknown"


STATUS_LABELS: dict[OverallStatus, str] = {
    OverallStatus.OPERATIONAL: "All Systems Operational",
    OverallStatus.DEGRADED: "Partially Degraded Service",
    OverallStatus.OUTAGE: "Major Outage",
    OverallStatus.MAINTENANCE: "Under Maintenance",
    OverallStatus.PAUSED: "All Monitors Paused",
    OverallStatus.UNKNOWN: "No Data",
}


@dataclasses.dataclass(slots=True)
class Heartbeat:
    """Single heartbeat sample of a monitor."""

    status: MonitorState
    time: str | None
    ping: float | None
    message: str
    important: bool


@dataclasses.dataclass(slots=True)
class Monitor:
    """Monitor as listed on a status page."""

    id: int
    name: str
    type: str
    url: str | None
    active: bool
    status: MonitorState
    message: str
    ping: float | None
    avg_ping: float | None
    uptime_24h: float | None
    uptime_30d: float | None
    heartbeats: list[Heartbeat]


@dataclasses.dataclass(slots=True)
class Group:
    """Group of monitors inside a status page."""

    id: int
    name: str
    status: OverallStatus
    uptime_24h: float | None
    monitors: list[Monitor]


@dataclasses.dataclass(slots=True)
class StatusPage:
    """Uptime Kuma status page and the groups it publishes."""

    id: int
    slug: str
    title: str
    description: str | None
    published: bool
    status: OverallStatus
    uptime_24h: float | None
    groups: list[Group]
    error: str | None


@dataclasses.dataclass(slots=True)
class Snapshot:
    """Complete status readout of an Uptime Kuma instance."""

    url: str
    generated_at: str
    version: str | None
    status: OverallStatus
    uptime_24h: float | None
    monitor_counts: dict[str, int]
    pages: list[StatusPage]


def status_label(status: OverallStatus) -> str:
    """Return the human readable label of an aggregated status."""
    return STATUS_LABELS[status]


def aggregate_status(monitors: list[Monitor]) -> OverallStatus:
    """Aggregate monitor states into a single status page verdict."""
    states = [monitor.status for monitor in monitors if monitor.status is not MonitorState.PAUSED]
    if not states:
        return OverallStatus.PAUSED if monitors else OverallStatus.UNKNOWN

    down = states.count(MonitorState.DOWN)
    if down == len(states):
        return OverallStatus.OUTAGE
    if down or MonitorState.PENDING in states:
        return OverallStatus.DEGRADED
    if MonitorState.MAINTENANCE in states:
        return OverallStatus.MAINTENANCE
    if MonitorState.UNKNOWN in states:
        return OverallStatus.UNKNOWN
    return OverallStatus.OPERATIONAL


def average_uptime(monitors: list[Monitor]) -> float | None:
    """Average the 24 hour uptime of the monitors that report one, ignoring paused ones."""
    values = [
        monitor.uptime_24h
        for monitor in monitors
        if monitor.uptime_24h is not None and monitor.status is not MonitorState.PAUSED
    ]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def count_states(monitors: list[Monitor]) -> dict[str, int]:
    """Count monitors per state, keyed by state value."""
    counts = {state.value: 0 for state in MonitorState}
    for monitor in monitors:
        counts[monitor.status.value] += 1
    return counts
