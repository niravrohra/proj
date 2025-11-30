from typing import Optional

from db import db_transaction


def _next_card_id(conn) -> int:
    row = conn.execute("SELECT COALESCE(MAX(Card_id), 0) + 1 FROM BORROWER").fetchone()
    return row[0]


def create_borrower(
    conn,
    ssn: str,
    name: str,
    address: str,
    phone: Optional[str] = None,
) -> int:
    ssn = (ssn or "").strip()
    name = (name or "").strip()
    address = (address or "").strip()
    phone = (phone or "").strip() or None

    if not ssn or not name or not address:
        raise ValueError("SSN, name, and address are required")

    with db_transaction(conn):
        if conn.execute("SELECT 1 FROM BORROWER WHERE Ssn = ?", (ssn,)).fetchone():
            raise ValueError("Borrower with this SSN already exists")

        card_id = _next_card_id(conn)
        conn.execute(
            "INSERT INTO BORROWER(Card_id, Ssn, Bname, Address, Phone) VALUES (?, ?, ?, ?, ?)",
            (card_id, ssn, name, address, phone),
        )
        return card_id
