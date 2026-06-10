from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.presentation.config import create_config_router


def test_get_public_config_only_exposes_seller_address() -> None:
    seller_address = "0x1234567890123456789012345678901234567890"

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.seller_address = seller_address
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(create_config_router())

    with TestClient(app) as client:
        response = client.get("/config")

    assert response.status_code == 200
    assert response.json() == {"seller_address": seller_address}
