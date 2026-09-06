from fastapi import APIRouter, HTTPException

from app.agents.agent import run_agent
from app.schemas.chat import ChatRequest
from app.services.conversation_service import (
    get_recent_messages,
    save_message
)


router = APIRouter(
    prefix="/chat",
    tags=["AI Retail Agent"]
)


@router.post("/")
def chat_with_agent(request: ChatRequest):
    """
    Send a customer message to the local retail AI agent
    with persistent conversation context.
    """

    try:
        message = request.message.strip()

        if not message:
            raise ValueError(
                "User message cannot be empty"
            )

        conversation_history = get_recent_messages(
            request.user_id,
            limit=10
        )

        save_message(
            user_id=request.user_id,
            role="user",
            content=message
        )

        result = run_agent(
            message,
            user_id=request.user_id,
            conversation_history=conversation_history
        )

        if result.get("success") is True:
            save_message(
                user_id=request.user_id,
                role="assistant",
                content=result.get("reply", "")
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