from datetime import UTC, datetime

from app.domain.events import NewEvent, NewTicketCategory
from app.infrastructure.database import SQLiteTicketingRepository


def test_create_and_get_event(tmp_path) -> None:
    repository = SQLiteTicketingRepository(str(tmp_path / "test.db"))
    repository.initialize()
    starts_at = datetime(2026, 9, 20, 20, tzinfo=UTC)

    created = repository.create(NewEvent("Concert", "Live concert", starts_at))
    retrieved = repository.get(created.id)

    assert retrieved == created
    assert repository.list_events() == [created]


def test_create_and_list_ticket_categories(tmp_path) -> None:
    repository = SQLiteTicketingRepository(str(tmp_path / "test.db"))
    repository.initialize()
    event = repository.create(
        NewEvent(
            "Concert",
            "Live concert",
            datetime(2026, 9, 20, 20, tzinfo=UTC),
        )
    )

    category = repository.create_category(
        NewTicketCategory(
            event_id=event.id,
            title="VIP",
            description="VIP entrance",
            price_wei=10**16,
            max_supply=100,
            image_filename="vip.png",
            image_content=b"image",
            image_content_type="image/png",
            image_ipfs_uri="ipfs://image-cid",
            metadata_ipfs_uri="ipfs://metadata-cid",
        )
    )

    assert repository.list_categories(event.id) == [category]
    assert repository.get_category(category.id) == category
