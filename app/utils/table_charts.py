from sqlalchemy import func
from sqlalchemy.orm import Session
from collections import Counter
import json
from app.models.table import Table


def get_capacity_distribution_chart(db: Session) -> list[dict]:

    rows = (
        db.query(
            Table.capacity,
            func.count(Table.id).label("tables_count"),
        )
        .group_by(Table.capacity)
        .order_by(Table.capacity.asc())
        .all()
    )

    return [
        {
            "key": capacity,
            "value": tables_count,
        }
        for capacity, tables_count in rows
    ]


def get_tags_distribution_chart(db: Session) -> list[dict]:

    counter = Counter()

    rows = db.query(Table.tags).all()

    for (tags,) in rows:

        if not tags:
            continue

        if isinstance(tags, str):
            tags = json.loads(tags)

        for tag in tags:
            counter[tag] += 1

    return [
        {
            "key": tag,
            "value": count,
        }
        for tag, count in sorted(counter.items())
    ]

