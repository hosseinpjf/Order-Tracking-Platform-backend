from collections import defaultdict
from datetime import date, datetime, timedelta
from sqlalchemy import func
from sqlalchemy.orm import Session


def get_chart_group_type(
    from_date: datetime,
    to_date: datetime,
):
    if to_date < from_date:
        raise ValueError("to_date must be greater than from_date")
    
    days = (to_date.date() - from_date.date()).days

    if days <= 31:
        return "day"

    if days <= 180:
        return "week"

    return "month"


def get_daily_group_expression(db: Session, created_at):

    dialect = db.bind.dialect.name

    if dialect == "postgresql":
        return func.to_char(created_at, "YYYY-MM-DD")

    return func.strftime("%Y-%m-%d", created_at)


def _bucket_key(day: date, group_type: str) -> str:

    if group_type == "day":
        return day.strftime("%Y-%m-%d")

    if group_type == "week":
        iso = day.isocalendar()
        return f"{iso.year}-{iso.week:02d}"

    if group_type == "month":
        return f"{day.year}-{day.month:02d}"

    raise ValueError(f"Invalid group type: {group_type}")


def merge_daily_rows(rows, group_type: str, value_key: str) -> dict[str, float]:

    buckets: dict[str, float] = defaultdict(float)

    for row in rows:
        day = datetime.strptime(row.key, "%Y-%m-%d").date()
        key = _bucket_key(day, group_type)
        buckets[key] += float(getattr(row, value_key) or 0)

    return buckets


def fill_missing_periods(
    buckets: dict[str, float],
    from_date: datetime,
    to_date: datetime,
    group_type: str,
) -> list[dict]:

    result = []

    if group_type == "day":

        current = from_date.date()

        while current <= to_date.date():

            key = current.strftime("%Y-%m-%d")

            result.append({
                "key": key,
                "value": buckets.get(key, 0.0)
            })

            current += timedelta(days=1)

        return result

    elif group_type == "week":

        current = from_date.date() - timedelta(days=from_date.weekday())
        end = to_date.date() - timedelta(days=to_date.weekday())

        while current <= end:

            iso = current.isocalendar()

            key = f"{iso.year}-{iso.week:02d}"

            result.append({
                "key": key,
                "value": buckets.get(key, 0.0)
            })

            current += timedelta(days=7)

        return result

    elif group_type == "month":

        current_year = from_date.year
        current_month = from_date.month

        while (current_year, current_month) <= (to_date.year, to_date.month):

            key = f"{current_year}-{current_month:02d}"

            result.append({
                "key": key,
                "value": buckets.get(key, 0.0)
            })

            current_month += 1

            if current_month > 12:
                current_month = 1
                current_year += 1

        return result

    raise ValueError(f"Invalid group type: {group_type}")


def normalize_datetime(dt: datetime) -> datetime:

    if dt.tzinfo is not None:
        return dt.astimezone().replace(tzinfo=None)

    return dt

