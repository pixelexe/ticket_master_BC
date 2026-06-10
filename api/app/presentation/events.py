from datetime import datetime

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    Request,
    UploadFile,
    status,
)
from pydantic import BaseModel, ConfigDict, Field

from app.domain.events import (
    BlockchainDeploymentError,
    Event,
    EventNotFoundError,
    EventRepository,
    EventService,
    MetadataStorageError,
    NewEvent,
    NewTicketCategory,
    TicketCategory,
    TicketCategoryNotFoundError,
    TicketContractDeployer,
    TicketMetadataStorage,
    TicketMintError,
    TicketMinter,
    TicketPayment,
    TicketPaymentResult,
)


class EventCreate(BaseModel):
    title: str = Field(min_length=1, max_length=120)
    description: str = Field(min_length=1, max_length=2_000)
    starts_at: datetime
    banner_ipfs_uri: str | None = None


class EventResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str
    starts_at: datetime
    banner_ipfs_uri: str | None


class TicketCategoryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    event_id: int
    title: str
    description: str
    price_wei: int
    max_supply: int
    contract_address: str | None
    image_ipfs_uri: str | None
    metadata_ipfs_uri: str | None


class TicketPaymentRequest(BaseModel):
    category_id: int = Field(gt=0)
    buyer_address: str = Field(pattern=r"^0x[a-fA-F0-9]{40}$")
    card_number: str = Field(min_length=12, max_length=19)


class TicketPaymentResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    category_id: int
    buyer_address: str
    token_id: int
    transaction_hash: str


def get_event_repository(request: Request) -> EventRepository:
    return request.app.state.ticketing_repository


def get_ticket_contract_deployer(request: Request) -> TicketContractDeployer:
    return request.app.state.ticket_contract_deployer


def get_ticket_metadata_storage(request: Request) -> TicketMetadataStorage:
    return request.app.state.ticket_metadata_storage


def get_ticket_minter(request: Request) -> TicketMinter:
    return request.app.state.ticket_minter


def get_event_service(
    repository: EventRepository = Depends(get_event_repository),
    contract_deployer: TicketContractDeployer = Depends(
        get_ticket_contract_deployer
    ),
    metadata_storage: TicketMetadataStorage = Depends(
        get_ticket_metadata_storage
    ),
    ticket_minter: TicketMinter = Depends(get_ticket_minter),
) -> EventService:
    return EventService(
        repository,
        contract_deployer,
        metadata_storage,
        ticket_minter,
    )


def create_events_router() -> APIRouter:
    router = APIRouter(prefix="/events", tags=["events"])

    @router.post(
        "/pay",
        response_model=TicketPaymentResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def pay_for_ticket(
        payload: TicketPaymentRequest,
        service: EventService = Depends(get_event_service),
    ) -> TicketPaymentResult:
        try:
            return service.pay_for_ticket(
                TicketPayment(
                    category_id=payload.category_id,
                    buyer_address=payload.buyer_address,
                    card_number=payload.card_number,
                )
            )
        except TicketCategoryNotFoundError as error:
            raise HTTPException(
                status_code=404,
                detail="Ticket category not found",
            ) from error
        except TicketMintError as error:
            raise HTTPException(
                status_code=502,
                detail="Ticket mint failed",
            ) from error

    @router.post("", response_model=EventResponse, status_code=status.HTTP_201_CREATED)
    def create_event(
        payload: EventCreate,
        service: EventService = Depends(get_event_service),
    ) -> Event:
        return service.create_event(
            NewEvent(
                title=payload.title,
                description=payload.description,
                starts_at=payload.starts_at,
                banner_ipfs_uri=payload.banner_ipfs_uri,
            )
        )

    @router.get("", response_model=list[EventResponse])
    def list_events(
        service: EventService = Depends(get_event_service),
    ) -> list[Event]:
        return service.list_events()

    @router.get("/{event_id}", response_model=EventResponse)
    def get_event(
        event_id: int,
        service: EventService = Depends(get_event_service),
    ) -> Event:
        try:
            return service.get_event(event_id)
        except EventNotFoundError as error:
            raise HTTPException(status_code=404, detail="Event not found") from error

    @router.post(
        "/{event_id}/ticket-categories",
        response_model=TicketCategoryResponse,
        status_code=status.HTTP_201_CREATED,
    )
    def create_ticket_category(
        event_id: int,
        title: str = Form(min_length=1, max_length=120),
        description: str = Form(min_length=1, max_length=2_000),
        price_wei: int = Form(gt=0),
        max_supply: int = Form(gt=0),
        image: UploadFile = File(),
        service: EventService = Depends(get_event_service),
    ) -> TicketCategory:
        try:
            image_content = image.file.read()
            if not image_content:
                raise HTTPException(
                    status_code=422,
                    detail="Ticket image is empty",
                )
            return service.create_ticket_category(
                NewTicketCategory(
                    event_id=event_id,
                    title=title,
                    description=description,
                    price_wei=price_wei,
                    max_supply=max_supply,
                    image_filename=image.filename or "ticket-image",
                    image_content=image_content,
                    image_content_type=(
                        image.content_type or "application/octet-stream"
                    ),
                )
            )
        except EventNotFoundError as error:
            raise HTTPException(status_code=404, detail="Event not found") from error
        except BlockchainDeploymentError as error:
            raise HTTPException(
                status_code=502,
                detail="Ticket contract deployment failed",
            ) from error
        except MetadataStorageError as error:
            raise HTTPException(
                status_code=502,
                detail="Ticket metadata upload failed",
            ) from error

    @router.get(
        "/{event_id}/ticket-categories",
        response_model=list[TicketCategoryResponse],
    )
    def list_ticket_categories(
        event_id: int,
        service: EventService = Depends(get_event_service),
    ) -> list[TicketCategory]:
        try:
            return service.list_ticket_categories(event_id)
        except EventNotFoundError as error:
            raise HTTPException(status_code=404, detail="Event not found") from error

    return router
