try:
    from sentry_sdk import metrics as _metrics
except ImportError:
    _metrics = None


def emit(event: str, **attributes) -> None:
    if _metrics is None:
        return
    cleaned = {k: v for k, v in attributes.items() if v is not None}
    _metrics.count(event, 1, attributes=cleaned or None)
