from fastapi import APIRouter, HTTPException

from app.schemas.support import (
    CreateSupportRequest,
    UpdateSupportRequest
)

from app.services.support_service import (
    create_support_request,
    get_support_requests,
    update_support_request
)


router = APIRouter(
    prefix="/support",
    tags=["Customer Support"]
)


@router.post("/")
def create_request(request: CreateSupportRequest):
    try:
        support_request = create_support_request(
            user_id=request.user_id,
            message=request.message,
            reason=request.reason,
            priority=request.priority
        )

        return {
            "success": True,
            "request": support_request
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.get("/{user_id}")
def get_requests(user_id: int):
    try:
        requests = get_support_requests(user_id)

        return {
            "success": True,
            "requests": requests
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


@router.patch("/{request_id}")
def update_request(
    request_id: int,
    request: UpdateSupportRequest
):
    try:
        updated_request = update_support_request(
            request_id=request_id,
            status=request.status,
            resolution=request.resolution
        )

        return {
            "success": True,
            "request": updated_request
        }

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )