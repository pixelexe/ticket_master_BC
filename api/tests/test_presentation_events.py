from contextlib import asynccontextmanager
from datetime import UTC, datetime

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.domain.events import Event, TicketCategory
from app.presentation.events import (
    create_events_router,
    get_event_repository,
    get_ticket_contract_deployer,
    get_ticket_minter,
    get_ticket_metadata_storage,
)


class InMemoryEventRepository:
    def __init__(self):
        self.events: dict[int, Event] = {}
        self.categories: dict[int, list[TicketCategory]] = {}

    def create(self, event):
        created = Event(
            id=len(self.events) + 1,
            title=event.title,
            description=event.description,
            starts_at=event.starts_at,
            banner_ipfs_uri=event.banner_ipfs_uri,
        )
        self.events[created.id] = created
        return created

    def get(self, event_id):
        return self.events.get(event_id)

    def list_events(self):
        return list(self.events.values())

    def create_category(self, category):
        created = TicketCategory(
            id=sum(len(items) for items in self.categories.values()) + 1,
            event_id=category.event_id,
            title=category.title,
            description=category.description,
            price_wei=category.price_wei,
            max_supply=category.max_supply,
            contract_address=category.contract_address,
            image_ipfs_uri=category.image_ipfs_uri,
            metadata_ipfs_uri=category.metadata_ipfs_uri,
        )
        self.categories.setdefault(category.event_id, []).append(created)
        return created

    def list_categories(self, event_id):
        return self.categories.get(event_id, [])

    def get_category(self, category_id):
        return next(
            (
                category
                for categories in self.categories.values()
                for category in categories
                if category.id == category_id
            ),
            None,
        )


def create_test_client() -> TestClient:
    repository = InMemoryEventRepository()
    contract_deployer = MockContractDeployer()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        yield

    app = FastAPI(lifespan=lifespan)
    app.include_router(create_events_router())
    app.dependency_overrides[get_event_repository] = lambda: repository
    app.dependency_overrides[get_ticket_contract_deployer] = (
        lambda: contract_deployer
    )
    app.dependency_overrides[get_ticket_metadata_storage] = (
        lambda: MockMetadataStorage()
    )
    app.dependency_overrides[get_ticket_minter] = lambda: MockTicketMinter()
    return TestClient(app)


class MockContractDeployer:
    def deploy(self, name, symbol, price_wei, max_supply, metadata_uri):
        return "0x1234567890123456789012345678901234567890"


class MockMetadataStorage:
    def pin_ticket_metadata(
        self,
        title,
        description,
        image_filename,
        image_content,
        image_content_type,
    ):
        return "ipfs://image-cid", "ipfs://metadata-cid"


class MockTicketMinter:
    def mint_for(self, contract_address, buyer_address):
        return 3, "0xtransaction"


def test_create_then_get_event() -> None:
    starts_at = datetime(2026, 9, 20, 20, tzinfo=UTC)

    with create_test_client() as client:
        create_response = client.post(
            "/events",
            json={
                "title": "Concert",
                "description": "Live concert",
                "starts_at": starts_at.isoformat(),
            },
        )
        get_response = client.get("/events/1")

    assert create_response.status_code == 201
    assert create_response.json()["title"] == "Concert"
    assert get_response.status_code == 200
    assert get_response.json() == create_response.json()


def test_list_events() -> None:
    with create_test_client() as client:
        client.post(
            "/events",
            json={
                "title": "Concert",
                "description": "Live concert",
                "starts_at": "2026-09-20T20:00:00+02:00",
            },
        )
        response = client.get("/events")

    assert response.status_code == 200
    assert response.json()[0]["title"] == "Concert"


def test_get_unknown_event_returns_404() -> None:
    with create_test_client() as client:
        response = client.get("/events/999")

    assert response.status_code == 404
    assert response.json() == {"detail": "Event not found"}


def test_create_then_list_ticket_category() -> None:
    with create_test_client() as client:
        client.post(
            "/events",
            json={
                "title": "Concert",
                "description": "Live concert",
                "starts_at": "2026-09-20T20:00:00+02:00",
            },
        )
        create_response = client.post(
            "/events/1/ticket-categories",
            data={
                "title": "VIP",
                "description": "VIP entrance",
                "price_wei": str(10**16),
                "max_supply": "100",
            },
            files={"image": ("vip.png", b"image", "image/png")},
        )
        list_response = client.get("/events/1/ticket-categories")

    assert create_response.status_code == 201
    assert create_response.json()["contract_address"] == (
        "0x1234567890123456789012345678901234567890"
    )
    assert create_response.json()["image_ipfs_uri"] == "ipfs://image-cid"
    assert create_response.json()["metadata_ipfs_uri"] == "ipfs://metadata-cid"
    assert list_response.status_code == 200
    assert list_response.json() == [create_response.json()]


def test_fake_card_payment_mints_ticket() -> None:
    with create_test_client() as client:
        client.post(
            "/events",
            json={
                "title": "Concert",
                "description": "Live concert",
                "starts_at": "2026-09-20T20:00:00+02:00",
            },
        )
        client.post(
            "/events/1/ticket-categories",
            data={
                "title": "VIP",
                "description": "VIP entrance",
                "price_wei": str(10**16),
                "max_supply": "100",
            },
            files={"image": ("vip.png", b"image", "image/png")},
        )

        response = client.post(
            "/events/pay",
            json={
                "category_id": 1,
                "buyer_address": "0xDD91599A58d1FC1937F2Fef25A3759033fbB6D60",
                "card_number": "4242424242424242",
            },
        )

    assert response.status_code == 201
    assert response.json()["token_id"] == 3
    assert response.json()["transaction_hash"] == "0xtransaction"
