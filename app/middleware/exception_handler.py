from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse

def response_handler(status: bool, message: str = None, data: dict = None, status_code: int = None):
    return {
        "status": status,
        "message": message,
        "data": data,
        "status_code": status_code
    }

async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content=response_handler(
            status=False,
            message=exc.detail if isinstance(exc.detail, str) else exc.detail.get("message"),
            data=None,
            status_code=exc.status_code
        )
    )

async def general_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content=response_handler(
            status=False,
            message="Internal server error",
            data=None,
            status_code=500
        )
    )