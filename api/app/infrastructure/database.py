import sqlite3
from datetime import datetime

from app.domain.events import Event, NewEvent, NewTicketCategory, TicketCategory


class SQLiteTicketingRepository:
    def __init__(self, database_path: str):
        self.database_path = database_path

    def initialize(self) -> None:
        with self._connect() as connection:
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    starts_at TEXT NOT NULL,
                    banner_ipfs_uri TEXT
                )
                """
            )
            connection.execute(
                """
                CREATE TABLE IF NOT EXISTS ticket_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id INTEGER NOT NULL,
                    title TEXT NOT NULL,
                    description TEXT NOT NULL,
                    price_wei INTEGER NOT NULL,
                    max_supply INTEGER NOT NULL,
                    contract_address TEXT,
                    image_ipfs_uri TEXT,
                    metadata_ipfs_uri TEXT,
                    FOREIGN KEY (event_id) REFERENCES events(id)
                )
                """
            )
            self._add_column_if_missing(
                connection,
                "ticket_categories",
                "image_ipfs_uri",
                "TEXT",
            )
            self._add_column_if_missing(
                connection,
                "ticket_categories",
                "metadata_ipfs_uri",
                "TEXT",
            )

    def create(self, event: NewEvent) -> Event:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO events (title, description, starts_at, banner_ipfs_uri)
                VALUES (?, ?, ?, ?)
                """,
                (
                    event.title,
                    event.description,
                    event.starts_at.isoformat(),
                    event.banner_ipfs_uri,
                ),
            )
            event_id = cursor.lastrowid

        if event_id is None:
            raise RuntimeError("SQLite did not return the created event id")

        return Event(
            id=event_id,
            title=event.title,
            description=event.description,
            starts_at=event.starts_at,
            banner_ipfs_uri=event.banner_ipfs_uri,
        )

    def get(self, event_id: int) -> Event | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, title, description, starts_at, banner_ipfs_uri
                FROM events
                WHERE id = ?
                """,
                (event_id,),
            ).fetchone()

        if row is None:
            return None

        return Event(
            id=row["id"],
            title=row["title"],
            description=row["description"],
            starts_at=datetime.fromisoformat(row["starts_at"]),
            banner_ipfs_uri=row["banner_ipfs_uri"],
        )

    def list_events(self) -> list[Event]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, title, description, starts_at, banner_ipfs_uri
                FROM events
                ORDER BY starts_at, id
                """
            ).fetchall()

        return [
            Event(
                id=row["id"],
                title=row["title"],
                description=row["description"],
                starts_at=datetime.fromisoformat(row["starts_at"]),
                banner_ipfs_uri=row["banner_ipfs_uri"],
            )
            for row in rows
        ]

    def create_category(self, category: NewTicketCategory) -> TicketCategory:
        with self._connect() as connection:
            cursor = connection.execute(
                """
                INSERT INTO ticket_categories (
                    event_id,
                    title,
                    description,
                    price_wei,
                    max_supply,
                    contract_address,
                    image_ipfs_uri,
                    metadata_ipfs_uri
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    category.event_id,
                    category.title,
                    category.description,
                    category.price_wei,
                    category.max_supply,
                    category.contract_address,
                    category.image_ipfs_uri,
                    category.metadata_ipfs_uri,
                ),
            )
            category_id = cursor.lastrowid

        if category_id is None:
            raise RuntimeError("SQLite did not return the created category id")

        return TicketCategory(
            id=category_id,
            event_id=category.event_id,
            title=category.title,
            description=category.description,
            price_wei=category.price_wei,
            max_supply=category.max_supply,
            contract_address=category.contract_address,
            image_ipfs_uri=category.image_ipfs_uri,
            metadata_ipfs_uri=category.metadata_ipfs_uri,
        )

    def list_categories(self, event_id: int) -> list[TicketCategory]:
        with self._connect() as connection:
            rows = connection.execute(
                """
                SELECT id, event_id, title, description, price_wei, max_supply,
                       contract_address, image_ipfs_uri, metadata_ipfs_uri
                FROM ticket_categories
                WHERE event_id = ?
                ORDER BY id
                """,
                (event_id,),
            ).fetchall()

        return [
            TicketCategory(
                id=row["id"],
                event_id=row["event_id"],
                title=row["title"],
                description=row["description"],
                price_wei=row["price_wei"],
                max_supply=row["max_supply"],
                contract_address=row["contract_address"],
                image_ipfs_uri=row["image_ipfs_uri"],
                metadata_ipfs_uri=row["metadata_ipfs_uri"],
            )
            for row in rows
        ]

    def get_category(self, category_id: int) -> TicketCategory | None:
        with self._connect() as connection:
            row = connection.execute(
                """
                SELECT id, event_id, title, description, price_wei, max_supply,
                       contract_address, image_ipfs_uri, metadata_ipfs_uri
                FROM ticket_categories
                WHERE id = ?
                """,
                (category_id,),
            ).fetchone()

        if row is None:
            return None

        return TicketCategory(
            id=row["id"],
            event_id=row["event_id"],
            title=row["title"],
            description=row["description"],
            price_wei=row["price_wei"],
            max_supply=row["max_supply"],
            contract_address=row["contract_address"],
            image_ipfs_uri=row["image_ipfs_uri"],
            metadata_ipfs_uri=row["metadata_ipfs_uri"],
        )

    def _connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database_path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        return connection

    @staticmethod
    def _add_column_if_missing(
        connection: sqlite3.Connection,
        table: str,
        column: str,
        column_type: str,
    ) -> None:
        columns = {
            row["name"]
            for row in connection.execute(f"PRAGMA table_info({table})")
        }
        if column not in columns:
            connection.execute(
                f"ALTER TABLE {table} ADD COLUMN {column} {column_type}"
            )
