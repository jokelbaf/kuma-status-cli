"""Terminal rendering of a status snapshot."""

import itertools

import rich.cells
import rich.console
import rich.text

import kuma_status_cli.models as models

BEAT = "█"
DOT = "●"
ARROW = "->"
ELLIPSIS = "..."

ACCENT = "#7C83FF"
MUTED = "#8B84A8"
SUBTLE = "#5B5470"

STATE_COLORS: dict[models.MonitorState, str] = {
    models.MonitorState.UP: "#5CDD8B",
    models.MonitorState.DOWN: "#FF5370",
    models.MonitorState.PENDING: "#F8A306",
    models.MonitorState.MAINTENANCE: ACCENT,
    models.MonitorState.PAUSED: "#6B6580",
    models.MonitorState.UNKNOWN: "#4A4560",
}

STATUS_COLORS: dict[models.OverallStatus, str] = {
    models.OverallStatus.OPERATIONAL: "#5CDD8B",
    models.OverallStatus.DEGRADED: "#F8A306",
    models.OverallStatus.OUTAGE: "#FF5370",
    models.OverallStatus.MAINTENANCE: ACCENT,
    models.OverallStatus.PAUSED: "#6B6580",
    models.OverallStatus.UNKNOWN: "#6B6580",
}

INDENT = "  "
MIN_BAR = 10
MAX_NAME = 34
MIN_NAME = 12
UPTIME_WIDTH = 8
PING_WIDTH = 8
CHROME = len(INDENT) + 2 + 2 + 2 + UPTIME_WIDTH + 1 + PING_WIDTH


class Layout:
    """Column widths used to align every row of the report."""

    def __init__(self, console_width: int, beats: int) -> None:
        """Derive the bar and name widths that fit the console."""
        self.console = console_width
        budget = console_width - CHROME
        self.bar = max(MIN_BAR, min(beats, budget - MIN_NAME))
        self.name = max(MIN_NAME, min(MAX_NAME, budget - self.bar))
        self.width = CHROME + self.bar + self.name


def _fit(text: str, width: int) -> str:
    """Pad or ellipsize text to exactly the given cell width."""
    length = rich.cells.cell_len(text)
    if length <= width:
        return text + " " * (width - length)
    if width <= len(ELLIPSIS):
        return rich.cells.set_cell_size(text, max(width, 0))
    return rich.cells.set_cell_size(text, width - len(ELLIPSIS)) + ELLIPSIS


def _right(text: str, width: int) -> str:
    """Right align text within the given cell width."""
    return " " * max(width - rich.cells.cell_len(text), 0) + text


def _percent(value: float | None) -> str:
    """Format an uptime percentage for display."""
    return f"{value:.2f}%" if value is not None else "-"


def _ping(value: float | None) -> str:
    """Format a ping value in milliseconds for display."""
    return f"{value:.0f} ms" if value is not None else "-"


def _split_row(left: rich.text.Text, right: rich.text.Text, width: int) -> rich.text.Text:
    """Join a left and a right aligned fragment into one padded row."""
    gap = max(width - left.cell_len - right.cell_len, 1)
    row = rich.text.Text(INDENT, no_wrap=True)
    row.append_text(left)
    row.append(" " * gap)
    row.append_text(right)
    return row


def _beat_bar(monitor: models.Monitor, width: int) -> rich.text.Text:
    """Render the heartbeat bar of a monitor, padded to a fixed width."""
    bar = rich.text.Text(no_wrap=True)
    recent = monitor.heartbeats[-width:]
    if monitor.status is models.MonitorState.PAUSED:
        bar.append(BEAT * width, style=STATE_COLORS[models.MonitorState.PAUSED])
        return bar
    states = [models.MonitorState.UNKNOWN] * (width - len(recent)) + [beat.status for beat in recent]
    for state, group in itertools.groupby(states):
        bar.append(BEAT * len(list(group)), style=STATE_COLORS[state])
    return bar


def _monitor_row(monitor: models.Monitor, layout: Layout) -> rich.text.Text:
    """Render a single monitor as a dot, name, heartbeat bar, uptime and ping."""
    color = STATE_COLORS[monitor.status]
    row = rich.text.Text(INDENT, no_wrap=True)
    row.append(DOT, style=color)
    row.append(" ")
    row.append(
        _fit(monitor.name, layout.name),
        style=SUBTLE if monitor.status is models.MonitorState.PAUSED else "default",
    )
    row.append("  ")
    row.append_text(_beat_bar(monitor, layout.bar))
    row.append("  ")
    row.append(_right(_percent(monitor.uptime_24h), UPTIME_WIDTH), style=MUTED)
    row.append(" ")
    row.append(_right(_ping(monitor.ping), PING_WIDTH), style=SUBTLE)
    return row


def _message_row(monitor: models.Monitor, layout: Layout) -> rich.text.Text:
    """Render the last error message of a monitor beneath its row."""
    prefix = f"{INDENT}  {ARROW} "
    body = _fit(monitor.message, max(layout.width - len(prefix), 0)).rstrip()
    return rich.text.Text(prefix + body, style=STATE_COLORS[monitor.status], no_wrap=True)


def _header(snapshot: models.Snapshot, layout: Layout) -> list[rich.text.Text]:
    """Build the instance summary shown above the status pages."""
    title = rich.text.Text(INDENT, no_wrap=True)
    title.append(snapshot.url, style=f"bold {ACCENT}")
    if snapshot.version:
        title.append(f"  v{snapshot.version}", style=SUBTLE)

    summary = rich.text.Text(INDENT, no_wrap=True)
    summary.append(DOT, style=STATUS_COLORS[snapshot.status])
    summary.append(" ")
    summary.append(models.status_label(snapshot.status), style=f"bold {STATUS_COLORS[snapshot.status]}")

    for state in models.MonitorState:
        count = snapshot.monitor_counts[state.value]
        if count:
            summary.append("   ")
            summary.append(str(count), style=f"bold {STATE_COLORS[state]}")
            summary.append(f" {state.value}", style=MUTED)

    if snapshot.uptime_24h is not None:
        summary.append("   ")
        summary.append(_percent(snapshot.uptime_24h), style=f"bold {ACCENT}")
        summary.append(" avg 24h", style=MUTED)

    summary.truncate(layout.console, overflow="crop")
    return [title, summary]


def _page_rows(page: models.StatusPage, layout: Layout) -> list[rich.text.Text]:
    """Build every row of a status page section."""
    rows = [
        _split_row(
            rich.text.Text(page.title, style="bold"),
            rich.text.Text(models.status_label(page.status), style=STATUS_COLORS[page.status]),
            layout.width - len(INDENT),
        )
    ]
    if page.description:
        rows.append(rich.text.Text(INDENT + _fit(page.description, layout.width - len(INDENT)).rstrip(), style=MUTED))
    rows.append(rich.text.Text(INDENT + "-" * (layout.width - len(INDENT)), style=SUBTLE, no_wrap=True))

    if page.error:
        rows.append(rich.text.Text(f"{INDENT}{page.error}", style=STATE_COLORS[models.MonitorState.DOWN]))
        return rows
    if not page.groups:
        rows.append(rich.text.Text(f"{INDENT}This status page has no monitors.", style=MUTED))
        return rows

    for group in page.groups:
        rows.append(rich.text.Text())
        rows.append(
            _split_row(
                rich.text.Text(group.name, style=f"bold {ACCENT}"),
                rich.text.Text(_percent(group.uptime_24h), style=MUTED),
                layout.width - len(INDENT),
            )
        )
        for monitor in group.monitors:
            rows.append(_monitor_row(monitor, layout))
            if monitor.message and monitor.status in (models.MonitorState.DOWN, models.MonitorState.PENDING):
                rows.append(_message_row(monitor, layout))
    return rows


def render(console: rich.console.Console, snapshot: models.Snapshot, beats: int) -> None:
    """Print a full status snapshot to the console."""
    layout = Layout(console.width, beats)
    rows = _header(snapshot, layout)

    if snapshot.pages:
        for page in snapshot.pages:
            rows.append(rich.text.Text())
            rows.extend(_page_rows(page, layout))
    else:
        rows.append(rich.text.Text())
        rows.append(rich.text.Text(f"{INDENT}No status pages are configured on this instance.", style=MUTED))

    console.print()
    for row in rows:
        console.print(row, no_wrap=True, crop=True)
    console.print()
