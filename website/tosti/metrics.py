from sentry_sdk import metrics


def emit(event: str, **attributes) -> None:
    cleaned = {k: v for k, v in attributes.items() if v is not None}
    metrics.count(event, 1, attributes=cleaned or None)
