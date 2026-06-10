from datetime import UTC, datetime
from unittest.mock import Mock

import pytest

from app.domain.events import (
    Event,
    EventNotFoundError,
    EventService,
    NewEvent,
    NewTicketCategory,
    TicketCategory,
    TicketCategoryNotFoundError,
    TicketPayment,
)


def test_create_event_delegates_to_repository() -> None:
    starts_at = datetime(2026, 9, 20, 20, tzinfo=UTC)
    new_event = NewEvent("Concert", "Live concert", starts_at)
    created_event = Event(1, "Concert", "Live concert", starts_at)
    repository = Mock()
    repository.create.return_value = created_event
    contract_deployer = Mock()
    metadata_storage = Mock()
    ticket_minter = Mock()

    result = EventService(
        repository, contract_deployer, metadata_storage, ticket_minter
    ).create_event(new_event)

    assert result == created_event
    repository.create.assert_called_once_with(new_event)


def test_get_event_raises_when_event_does_not_exist() -> None:
    repository = Mock()
    repository.get.return_value = None
    contract_deployer = Mock()
    metadata_storage = Mock()
    ticket_minter = Mock()

    with pytest.raises(EventNotFoundError):
        EventService(
            repository, contract_deployer, metadata_storage, ticket_minter
        ).get_event(999)


def test_create_ticket_category_requires_existing_event() -> None:
    repository = Mock()
    repository.get.return_value = None
    contract_deployer = Mock()
    metadata_storage = Mock()
    ticket_minter = Mock()
    category = NewTicketCategory(
        999,
        "VIP",
        "VIP entrance",
        10**16,
        100,
        "vip.png",
        b"image",
        "image/png",
    )

    with pytest.raises(EventNotFoundError):
        EventService(
            repository, contract_deployer, metadata_storage, ticket_minter
        ).create_ticket_category(category)

    repository.create_category.assert_not_called()
    contract_deployer.deploy.assert_not_called()
    metadata_storage.pin_ticket_metadata.assert_not_called()


def test_create_ticket_category_deploys_contract_before_saving() -> None:
    repository = Mock()
    repository.get.return_value = Event(
        1,
        "Concert",
        "Live concert",
        datetime(2026, 9, 20, 20, tzinfo=UTC),
    )
    contract_deployer = Mock()
    contract_deployer.deploy.return_value = "0x1234567890123456789012345678901234567890"
    metadata_storage = Mock()
    metadata_storage.pin_ticket_metadata.return_value = (
        "ipfs://image-cid",
        "ipfs://metadata-cid",
    )
    category = NewTicketCategory(
        1,
        "VIP Pass",
        "VIP entrance",
        10**16,
        100,
        "vip.png",
        b"image",
        "image/png",
    )
    ticket_minter = Mock()

    EventService(
        repository, contract_deployer, metadata_storage, ticket_minter
    ).create_ticket_category(category)

    metadata_storage.pin_ticket_metadata.assert_called_once()
    contract_deployer.deploy.assert_called_once_with(
        name="VIP Pass",
        symbol="VIPPA",
        price_wei=10**16,
        max_supply=100,
        metadata_uri="ipfs://metadata-cid",
    )
    saved_category = repository.create_category.call_args.args[0]
    assert saved_category.contract_address == contract_deployer.deploy.return_value
    assert saved_category.image_ipfs_uri == "ipfs://image-cid"
    assert saved_category.metadata_ipfs_uri == "ipfs://metadata-cid"


def test_pay_for_ticket_mints_for_buyer() -> None:
    repository = Mock()
    repository.get_category.return_value = TicketCategory(
        id=2,
        event_id=1,
        title="VIP",
        description="VIP entrance",
        price_wei=10**16,
        max_supply=100,
        contract_address="0x1234567890123456789012345678901234567890",
    )
    ticket_minter = Mock()
    ticket_minter.mint_for.return_value = (3, "0xtransaction")
    service = EventService(repository, Mock(), Mock(), ticket_minter)

    result = service.pay_for_ticket(
        TicketPayment(
            category_id=2,
            buyer_address="0xDD91599A58d1FC1937F2Fef25A3759033fbB6D60",
            card_number="4242424242424242",
        )
    )

    assert result.token_id == 3
    assert result.transaction_hash == "0xtransaction"
    ticket_minter.mint_for.assert_called_once_with(
        contract_address="0x1234567890123456789012345678901234567890",
        buyer_address="0xDD91599A58d1FC1937F2Fef25A3759033fbB6D60",
    )


def test_pay_for_ticket_rejects_unknown_category() -> None:
    repository = Mock()
    repository.get_category.return_value = None
    ticket_minter = Mock()
    service = EventService(repository, Mock(), Mock(), ticket_minter)

    with pytest.raises(TicketCategoryNotFoundError):
        service.pay_for_ticket(
            TicketPayment(
                category_id=999,
                buyer_address="0xDD91599A58d1FC1937F2Fef25A3759033fbB6D60",
                card_number="4242424242424242",
            )
        )

    ticket_minter.mint_for.assert_not_called()
