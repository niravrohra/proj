import csv
import re
from pathlib import Path
from typing import Iterable, Tuple

from db import get_connection

SCHEMA_FILE = Path("schema.sql")
BOOK_FILE = Path("book.csv")
AUTHORS_FILE = Path("authors.csv")
BOOK_AUTHORS_FILE = Path("book_authors.csv")
BORROWER_FILE = Path("borrower.csv")

DROP_STATEMENTS = """
DROP TABLE IF EXISTS FINES;
DROP TABLE IF EXISTS BOOK_LOANS;
DROP TABLE IF EXISTS BOOK_AUTHORS;
DROP TABLE IF EXISTS AUTHORS;
DROP TABLE IF EXISTS BORROWER;
DROP TABLE IF EXISTS BOOK;
"""


def _read_csv_rows(path: Path) -> Iterable[dict]:
    if not path.exists():
        raise FileNotFoundError(f"Missing required CSV: {path}")
    with path.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        yield from reader


def initialize_schema(conn) -> None:
    conn.executescript(DROP_STATEMENTS)
    conn.executescript(SCHEMA_FILE.read_text(encoding="utf-8"))


def load_book(conn) -> None:
    rows: Tuple[Tuple[str, str], ...] = tuple(
        (row["Isbn"].strip(), row["Title"].strip())
        for row in _read_csv_rows(BOOK_FILE)
        if row.get("Isbn") and row.get("Title")
    )
    conn.executemany("INSERT INTO BOOK(Isbn, Title) VALUES (?, ?)", rows)


def load_authors(conn) -> None:
    rows = [
        (int(row["Author_id"]), row["Name"].strip())
        for row in _read_csv_rows(AUTHORS_FILE)
        if row.get("Author_id") and row.get("Name")
    ]
    conn.executemany("INSERT INTO AUTHORS(Author_id, Name) VALUES (?, ?)", rows)


def load_book_authors(conn) -> None:
    rows = [
        (int(row["Author_id"]), row["Isbn"].strip())
        for row in _read_csv_rows(BOOK_AUTHORS_FILE)
        if row.get("Author_id") and row.get("Isbn")
    ]
    conn.executemany(
        "INSERT INTO BOOK_AUTHORS(Author_id, Isbn) VALUES (?, ?)",
        rows,
    )


def load_borrowers(conn) -> None:
    def _normalize_card(value: str) -> int:
        if value is None:
            raise ValueError("Card_id missing")
        digits = re.sub(r"\D", "", value)
        if not digits:
            raise ValueError(f"Card_id '{value}' has no digits")
        return int(digits)

    rows = [
        (
            _normalize_card(row["Card_id"]),
            row["Ssn"].strip(),
            row["Bname"].strip(),
            row["Address"].strip(),
            row.get("Phone", "").strip() or None,
        )
        for row in _read_csv_rows(BORROWER_FILE)
        if row.get("Card_id") and row.get("Ssn")
    ]
    conn.executemany(
        "INSERT INTO BORROWER(Card_id, Ssn, Bname, Address, Phone) VALUES (?, ?, ?, ?, ?)",
        rows,
    )


def load_all(conn) -> None:
    initialize_schema(conn)
    load_book(conn)
    load_authors(conn)
    load_book_authors(conn)
    load_borrowers(conn)
    conn.commit()


if __name__ == "__main__":
    with get_connection() as conn:
        load_all(conn)
        print("Database refreshed using normalized CSVs.")
