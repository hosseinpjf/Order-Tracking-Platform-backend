from datetime import datetime


def normalize_datetime(dt: datetime) -> datetime:

    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)

    return dt

