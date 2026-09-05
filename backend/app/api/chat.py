from fastapi import APIRouter, HTTPException

from app.agents.agent import run_agent
from app.schemas.chat import ChatRequest


router = APIRouter(
    prefix="/chat",
    tags=["AI Retail Agent"]
)


@router.post("/")
def chat_with_agent(request: ChatRequest):
    """
    Send a customer message to the local retail AI agent.
    """

    try:
        result = run_agent(
            request.message
        )

        return result

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=str(e)
        )

    except RuntimeError as e:
        raise HTTPException(
            status_code=503,
            detail=str(e)
        )

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )