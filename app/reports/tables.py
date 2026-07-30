from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, case
from app.db.session import get_db
from app.services.jwt_bearer import get_payload
from app.middleware.exception_handler import response_handler
from app.models.table import Table, TableStatus, TableTags


router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/table/kpi")
def get_table_summary(payload = Depends(get_payload), db: Session = Depends(get_db)):
    try:
        if payload["role"] != "admin":
            raise HTTPException(status_code=403, detail="Access denied")

        summary = (
            db.query(
                func.count(Table.id).label("total_tables"),
                func.sum(
                    case(
                        (Table.status == TableStatus.free, 1),
                        else_=0,
                    )
                ).label("free_tables"),
                func.sum(
                    case(
                        (Table.status == TableStatus.occupied, 1),
                        else_=0,
                    )
                ).label("occupied_tables"),
                func.sum(
                    case(
                        (Table.status == TableStatus.cleaning, 1),
                        else_=0,
                    )
                ).label("cleaning_tables"),
                func.sum(Table.capacity).label("total_capacity"),
                func.avg(Table.capacity).label("average_capacity"),
            )
            .first()
        )

        largest_table = (
            db.query(Table)
            .order_by(
                Table.capacity.desc(),
                Table.number.asc(),
            )
            .first()
        )

        smallest_table = (
            db.query(Table)
            .order_by(
                Table.capacity.asc(),
                Table.number.asc(),
            )
            .first()
        )

        return response_handler(
            status=True,
            message="Get table KPI report successful",
            data={
                "total_tables": summary.total_tables or 0,

                "free_tables": summary.free_tables or 0,
                "occupied_tables": summary.occupied_tables or 0,
                "cleaning_tables": summary.cleaning_tables or 0,

                "total_capacity": summary.total_capacity or 0,
                "average_capacity": round(summary.average_capacity or 0),

                "largest_table": (
                    {
                        "id": largest_table.id,
                        "number": largest_table.number,
                        "capacity": largest_table.capacity,
                    }
                    if largest_table
                    else None
                ),

                "smallest_table": (
                    {
                        "id": smallest_table.id,
                        "number": smallest_table.number,
                        "capacity": smallest_table.capacity,
                    }
                    if smallest_table
                    else None
                ),
            },
            status_code=200,
        )
    except HTTPException as http_error:
        raise http_error
    except Exception:
        raise HTTPException(status_code=500, detail="Get table KPI report failed")