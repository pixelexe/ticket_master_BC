from fastapi import APIRouter, Request
from pydantic import BaseModel


class PublicConfigResponse(BaseModel):
    seller_address: str


def create_config_router() -> APIRouter:
    router = APIRouter(prefix="/config", tags=["config"])

    @router.get("", response_model=PublicConfigResponse)
    def get_public_config(request: Request) -> PublicConfigResponse:
        return PublicConfigResponse(
            seller_address=request.app.state.seller_address,
        )

    return router
