import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from app.infrastructure.blockchain import Web3TicketContractDeployer
from app.infrastructure.database import SQLiteTicketingRepository
from app.infrastructure.pinata import PinataTicketMetadataStorage
from app.presentation.config import create_config_router
from app.presentation.events import create_events_router

PROJECT_ROOT = Path(__file__).resolve().parents[2]
CONTRACTS_ROOT = PROJECT_ROOT / "contracts"


@asynccontextmanager
async def lifespan(app: FastAPI):
    load_dotenv(CONTRACTS_ROOT / ".env")

    repository = SQLiteTicketingRepository("ticketing.db")
    repository.initialize()
    app.state.ticketing_repository = repository
    app.state.seller_address = os.environ["SELLER_ADDRESS"]
    app.state.ticket_contract_deployer = Web3TicketContractDeployer(
        rpc_url=os.environ["SEPOLIA_RPC_URL"],
        private_key=os.environ["PRIVATE_KEY"],
        seller_address=app.state.seller_address,
        artifact_path=CONTRACTS_ROOT
        / "out"
        / "Ticket.sol"
        / "Ticket.json",
    )
    app.state.ticket_minter = app.state.ticket_contract_deployer
    app.state.ticket_metadata_storage = PinataTicketMetadataStorage(
        os.environ.get("PINATA_JWT", "")
    )
    yield


app = FastAPI(
    title="Ticketing API",
    description="API for the NFT ticketing platform",
    version="0.1.0",
    lifespan=lifespan,
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:5173", "http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(create_config_router())
app.include_router(create_events_router())
