from dataclasses import dataclass
from datetime import datetime
from typing import Protocol


@dataclass(frozen=True)
class Event:
    id: int
    title: str
    description: str
    starts_at: datetime
    banner_ipfs_uri: str | None = None


@dataclass(frozen=True)
class TicketCategory:
    id: int
    event_id: int
    title: str
    description: str
    price_wei: int
    max_supply: int
    contract_address: str | None = None
    image_ipfs_uri: str | None = None
    metadata_ipfs_uri: str | None = None


@dataclass(frozen=True)
class TicketPayment:
    category_id: int
    buyer_address: str
    card_number: str


@dataclass(frozen=True)
class TicketPaymentResult:
    category_id: int
    buyer_address: str
    token_id: int
    transaction_hash: str


@dataclass(frozen=True)
class NewEvent:
    title: str
    description: str
    starts_at: datetime
    banner_ipfs_uri: str | None = None


@dataclass(frozen=True)
class NewTicketCategory:
    event_id: int
    title: str
    description: str
    price_wei: int
    max_supply: int
    image_filename: str
    image_content: bytes
    image_content_type: str
    contract_address: str | None = None
    image_ipfs_uri: str | None = None
    metadata_ipfs_uri: str | None = None


class EventNotFoundError(Exception):
    pass


class BlockchainDeploymentError(Exception):
    pass


class MetadataStorageError(Exception):
    pass


class TicketCategoryNotFoundError(Exception):
    pass


class TicketMintError(Exception):
    pass


class EventRepository(Protocol):
    def create(self, event: NewEvent) -> Event: ...

    def get(self, event_id: int) -> Event | None: ...

    def list_events(self) -> list[Event]: ...

    def create_category(self, category: NewTicketCategory) -> TicketCategory: ...

    def get_category(self, category_id: int) -> TicketCategory | None: ...

    def list_categories(self, event_id: int) -> list[TicketCategory]: ...


class TicketContractDeployer(Protocol):
    def deploy(
        self,
        name: str,
        symbol: str,
        price_wei: int,
        max_supply: int,
        metadata_uri: str,
    ) -> str: ...


class TicketMetadataStorage(Protocol):
    def pin_ticket_metadata(
        self,
        title: str,
        description: str,
        image_filename: str,
        image_content: bytes,
        image_content_type: str,
    ) -> tuple[str, str]: ...


class TicketMinter(Protocol):
    def mint_for(
        self,
        contract_address: str,
        buyer_address: str,
    ) -> tuple[int, str]: ...


class EventService:
    def __init__(
        self,
        repository: EventRepository,
        contract_deployer: TicketContractDeployer,
        metadata_storage: TicketMetadataStorage,
        ticket_minter: TicketMinter,
    ):
        self.repository = repository
        self.contract_deployer = contract_deployer
        self.metadata_storage = metadata_storage
        self.ticket_minter = ticket_minter

    def create_event(self, event: NewEvent) -> Event:
        return self.repository.create(event)

    def get_event(self, event_id: int) -> Event:
        event = self.repository.get(event_id)
        if event is None:
            raise EventNotFoundError(event_id)
        return event

    def list_events(self) -> list[Event]:
        return self.repository.list_events()

    def create_ticket_category(
        self, category: NewTicketCategory
    ) -> TicketCategory:
        self.get_event(category.event_id)
        image_ipfs_uri, metadata_ipfs_uri = (
            self.metadata_storage.pin_ticket_metadata(
                title=category.title,
                description=category.description,
                image_filename=category.image_filename,
                image_content=category.image_content,
                image_content_type=category.image_content_type,
            )
        )
        contract_address = self.contract_deployer.deploy(
            name=category.title,
            symbol=_ticket_symbol(category.title),
            price_wei=category.price_wei,
            max_supply=category.max_supply,
            metadata_uri=metadata_ipfs_uri,
        )
        return self.repository.create_category(
            NewTicketCategory(
                event_id=category.event_id,
                title=category.title,
                description=category.description,
                price_wei=category.price_wei,
                max_supply=category.max_supply,
                image_filename=category.image_filename,
                image_content=category.image_content,
                image_content_type=category.image_content_type,
                contract_address=contract_address,
                image_ipfs_uri=image_ipfs_uri,
                metadata_ipfs_uri=metadata_ipfs_uri,
            )
        )

    def list_ticket_categories(self, event_id: int) -> list[TicketCategory]:
        self.get_event(event_id)
        return self.repository.list_categories(event_id)

    def pay_for_ticket(self, payment: TicketPayment) -> TicketPaymentResult:
        category = self.repository.get_category(payment.category_id)
        if category is None or category.contract_address is None:
            raise TicketCategoryNotFoundError(payment.category_id)

        token_id, transaction_hash = self.ticket_minter.mint_for(
            contract_address=category.contract_address,
            buyer_address=payment.buyer_address,
        )
        return TicketPaymentResult(
            category_id=payment.category_id,
            buyer_address=payment.buyer_address,
            token_id=token_id,
            transaction_hash=transaction_hash,
        )


def _ticket_symbol(title: str) -> str:
    symbol = "".join(character for character in title.upper() if character.isalnum())
    return symbol[:5] or "TICKET"
