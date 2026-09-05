"""Fetching and assembling status data from an Uptime Kuma instance."""

import datetime
import typing

import requests
import uptime_kuma_api

import kuma_status_cli.config as config
import kuma_status_cli.models as models

UPTIME_24H = 24
UPTIME_30D = 720

RawDict = dict[str, typing.Any]
UptimeMap = dict[int, dict[int, typing.Any]]
PingMap = dict[int, typing.Any]
BeatMap = dict[int, list[RawDict]]

STATE_BY_CODE: dict[int, models.MonitorState] = {
    0: models.MonitorState.DOWN,
    1: models.MonitorState.UP,
    2: models.MonitorState.PENDING,
    3: models.MonitorState.MAINTENANCE,
}


class ClientError(Exception):
    """Raised when the Uptime Kuma instance cannot be queried."""


class Api(typing.Protocol):
    """Subset of the Uptime Kuma API this client relies on."""

    def login(self, username: str, password: str) -> object:
        """Authenticate against the instance."""
        ...

    def info(self) -> RawDict:
        """Return server information."""
        ...

    def get_monitors(self) -> list[RawDict]:
        """Return every configured monitor."""
        ...

    def get_heartbeats(self) -> BeatMap:
        """Return recent heartbeats per monitor id."""
        ...

    def uptime(self) -> UptimeMap:
        """Return uptime ratios per monitor id and window in hours."""
        ...

    def avg_ping(self) -> PingMap:
        """Return the average ping per monitor id."""
        ...

    def get_status_pages(self) -> list[RawDict]:
        """Return the summary of every status page."""
        ...

    def disconnect(self) -> None:
        """Close the connection."""
        ...


def _public_groups(base_url: str, slug: str, timeout: float) -> list[RawDict]:
    """Read the public group list of a status page over its HTTP endpoint."""
    response = requests.get(f"{base_url}/api/status-page/{slug}", timeout=timeout)
    response.raise_for_status()
    body = typing.cast(RawDict, response.json())
    groups = typing.cast(list[typing.Any], body.get("publicGroupList") or [])
    return [typing.cast(RawDict, group) for group in groups if isinstance(group, dict)]


def _connect(settings: config.Config, timeout: float) -> Api:
    """Open a connection to the Uptime Kuma instance."""
    try:
        return typing.cast(Api, uptime_kuma_api.UptimeKumaApi(settings.url, timeout=timeout))
    except Exception as error:
        raise ClientError(f"Could not connect to {settings.url}: {error}") from error


def _authenticate(api: Api, settings: config.Config) -> None:
    """Log in with the stored credentials."""
    try:
        api.login(settings.username, settings.password)
    except Exception as error:
        raise ClientError(f"Login failed for user '{settings.username}': {error}") from error


def _text(data: RawDict, key: str) -> str | None:
    """Return a stripped string field, or None when absent or empty."""
    value = data.get(key)
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _number(data: RawDict, key: str) -> float | None:
    """Return a numeric field as a float, or None when absent or invalid."""
    value = data.get(key)
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        return None
    try:
        return float(value)
    except ValueError:
        return None


def _flag(data: RawDict, key: str, default: bool = True) -> bool:
    """Return a boolean field that Uptime Kuma may encode as an integer."""
    value = data.get(key)
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    if isinstance(value, (int, float)):
        return bool(value)
    return default


def _state(code: object) -> models.MonitorState:
    """Map an Uptime Kuma status code to a monitor state."""
    if isinstance(code, bool) or not isinstance(code, (int, float)):
        return models.MonitorState.UNKNOWN
    return STATE_BY_CODE.get(int(code), models.MonitorState.UNKNOWN)


def _heartbeats(raw: list[RawDict], limit: int) -> list[models.Heartbeat]:
    """Convert the trailing heartbeat samples of a monitor."""
    recent = raw[-limit:] if limit > 0 else raw
    return [
        models.Heartbeat(
            status=_state(beat.get("status")),
            time=_text(beat, "time"),
            ping=_number(beat, "ping"),
            message=_text(beat, "msg") or "",
            important=_flag(beat, "important", default=False),
        )
        for beat in recent
    ]


def _uptime(uptimes: UptimeMap, monitor_id: int, hours: int) -> float | None:
    """Return the uptime ratio of a monitor over the given window, as a percentage."""
    entry = uptimes.get(monitor_id)
    if not entry:
        return None
    value = entry.get(hours)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return round(float(value) * 100, 4)


def _build_monitor(
    entry: RawDict,
    details: RawDict,
    heartbeats: BeatMap,
    uptimes: UptimeMap,
    avg_pings: PingMap,
    beats: int,
) -> models.Monitor:
    """Assemble a monitor from status page, monitor list and live event data."""
    monitor_id = int(entry["id"])
    beat_list = _heartbeats(heartbeats.get(monitor_id, []), beats)
    last = beat_list[-1] if beat_list else None
    active = _flag(details, "active") if details else True

    if not active:
        status = models.MonitorState.PAUSED
    elif last is not None:
        status = last.status
    else:
        status = models.MonitorState.UNKNOWN

    avg_ping = avg_pings.get(monitor_id)
    return models.Monitor(
        id=monitor_id,
        name=_text(details, "name") or _text(entry, "name") or f"Monitor {monitor_id}",
        type=_text(details, "type") or _text(entry, "type") or "unknown",
        url=_text(details, "url") if _flag(entry, "sendUrl", default=False) else None,
        active=active,
        status=status,
        message=last.message if last is not None else "",
        ping=last.ping if last is not None else None,
        avg_ping=float(avg_ping) if isinstance(avg_ping, (int, float)) and not isinstance(avg_ping, bool) else None,
        uptime_24h=_uptime(uptimes, monitor_id, UPTIME_24H) if active else None,
        uptime_30d=_uptime(uptimes, monitor_id, UPTIME_30D) if active else None,
        heartbeats=beat_list,
    )


def _build_page(
    summary: RawDict,
    raw_groups: list[RawDict],
    error: str | None,
    monitors: dict[int, RawDict],
    heartbeats: BeatMap,
    uptimes: UptimeMap,
    avg_pings: PingMap,
    beats: int,
) -> models.StatusPage:
    """Assemble a status page and its groups from the fetched payloads."""
    groups: list[models.Group] = []

    for raw_group in raw_groups:
        group_monitors = [
            _build_monitor(entry, monitors.get(int(entry["id"]), {}), heartbeats, uptimes, avg_pings, beats)
            for entry in list(raw_group.get("monitorList") or [])
            if entry.get("id") is not None
        ]
        group_monitors.sort(key=lambda monitor: monitor.status is models.MonitorState.PAUSED)
        groups.append(
            models.Group(
                id=int(raw_group.get("id") or 0),
                name=_text(raw_group, "name") or "Ungrouped",
                status=models.aggregate_status(group_monitors),
                uptime_24h=models.average_uptime(group_monitors),
                monitors=group_monitors,
            )
        )

    groups.sort(key=lambda group: group.status is models.OverallStatus.PAUSED)
    flat = [monitor for group in groups for monitor in group.monitors]
    return models.StatusPage(
        id=int(summary.get("id") or 0),
        slug=_text(summary, "slug") or "",
        title=_text(summary, "title") or _text(summary, "slug") or "Status page",
        description=_text(summary, "description"),
        published=_flag(summary, "published"),
        status=models.aggregate_status(flat),
        uptime_24h=models.average_uptime(flat),
        groups=groups,
        error=error,
    )


def fetch(settings: config.Config, beats: int = 40, timeout: float = 15.0) -> models.Snapshot:
    """Log in to Uptime Kuma and collect a full status snapshot."""
    api = _connect(settings, timeout)

    try:
        _authenticate(api, settings)

        try:
            monitor_list = api.get_monitors()
            heartbeats = api.get_heartbeats()
            uptimes = api.uptime()
            avg_pings = api.avg_ping()
            page_summaries = api.get_status_pages()
            info = api.info()
        except Exception as error:
            raise ClientError(f"Could not read data from {settings.url}: {error}") from error

        monitors = {int(item["id"]): item for item in monitor_list if item.get("id") is not None}
        pages: list[models.StatusPage] = []

        for summary in sorted(page_summaries, key=lambda item: str(item.get("title") or "")):
            slug = _text(summary, "slug")
            raw_groups: list[RawDict] = []
            error_text: str | None = None
            if slug is None:
                error_text = "Status page has no slug."
            elif not _flag(summary, "published"):
                error_text = "Status page is not published, so its monitors are not readable."
            else:
                try:
                    raw_groups = _public_groups(settings.url, slug, timeout)
                except Exception as error:
                    error_text = f"Could not load status page '{slug}': {error}"
            pages.append(_build_page(summary, raw_groups, error_text, monitors, heartbeats, uptimes, avg_pings, beats))
    finally:
        api.disconnect()

    pages.sort(key=lambda page: page.status is models.OverallStatus.PAUSED)
    flat = [monitor for page in pages for group in page.groups for monitor in group.monitors]
    return models.Snapshot(
        url=settings.url,
        generated_at=datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds"),
        version=_text(info, "version"),
        status=models.aggregate_status(flat),
        uptime_24h=models.average_uptime(flat),
        monitor_counts=models.count_states(flat),
        pages=pages,
    )


def check(settings: config.Config, timeout: float = 15.0) -> str | None:
    """Verify the credentials and return the Uptime Kuma version."""
    api = _connect(settings, timeout)
    try:
        _authenticate(api, settings)
        return _text(api.info(), "version")
    finally:
        api.disconnect()
