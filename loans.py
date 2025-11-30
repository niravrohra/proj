from datetime import date, timedelta
from typing import List, Optional

from db import db_transaction

MAX_ACTIVE_LOANS = 3

OPEN_LOANS_SELECT = """
SELECT
    bl.Loan_id,
    bl.Isbn,
    b.Title,
    bl.Card_id,
    bor.Bname,
    bl.Date_out,
    bl.Due_date
FROM BOOK_LOANS bl
JOIN BOOK b   ON bl.Isbn = b.Isbn
JOIN BORROWER bor ON bl.Card_id = bor.Card_id
"""


def checkout(conn, isbn: str, card_id: int) -> int:
    isbn = (isbn or "").strip()
    card_id = int(card_id)
    if not isbn:
        raise ValueError("ISBN is required")

    today = date.today()
    due = today + timedelta(days=14)

    with db_transaction(conn):
        cursor = conn.cursor()

        if not cursor.execute("SELECT 1 FROM BOOK WHERE Isbn = ?", (isbn,)).fetchone():
            raise ValueError("Book not found")

        if not cursor.execute("SELECT 1 FROM BORROWER WHERE Card_id = ?", (card_id,)).fetchone():
            raise ValueError("Borrower not found")

        active_loans = cursor.execute(
            "SELECT COUNT(*) FROM BOOK_LOANS WHERE Card_id = ? AND Date_in IS NULL",
            (card_id,),
        ).fetchone()[0]
        if active_loans >= MAX_ACTIVE_LOANS:
            raise ValueError("Borrower already has 3 books checked out")

        unpaid_fines = cursor.execute(
            """
            SELECT COUNT(*)
            FROM FINES f
            JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
            WHERE bl.Card_id = ? AND f.Paid = 0
            """,
            (card_id,),
        ).fetchone()[0]
        if unpaid_fines:
            raise ValueError("Borrower has unpaid fines")

        book_out = cursor.execute(
            "SELECT 1 FROM BOOK_LOANS WHERE Isbn = ? AND Date_in IS NULL",
            (isbn,),
        ).fetchone()
        if book_out:
            raise ValueError("Book is currently checked out")

        cursor.execute(
            """
            INSERT INTO BOOK_LOANS (Isbn, Card_id, Date_out, Due_date, Date_in)
            VALUES (?, ?, ?, ?, NULL)
            """,
            (isbn, card_id, today.isoformat(), due.isoformat()),
        )
        return cursor.lastrowid


def find_open_loans(
    conn,
    isbn: Optional[str] = None,
    card_id: Optional[int] = None,
    borrower_name: Optional[str] = None,
) -> List[dict]:
    isbn = (isbn or "").strip()
    borrower_name = (borrower_name or "").strip()
    conditions = ["bl.Date_in IS NULL"]
    params = []

    if isbn:
        conditions.append("LOWER(bl.Isbn) = LOWER(?)")
        params.append(isbn)
    if card_id is not None:
        conditions.append("bl.Card_id = ?")
        params.append(int(card_id))
    if borrower_name:
        conditions.append("LOWER(bor.Bname) LIKE ?")
        params.append(f"%{borrower_name.lower()}%")

    if len(conditions) == 1:
        raise ValueError("Provide at least one search parameter")

    where_clause = " WHERE " + " AND ".join(conditions)
    cursor = conn.cursor()
    cursor.execute(OPEN_LOANS_SELECT + where_clause + " ORDER BY bl.Due_date", params)
    return [dict(row) for row in cursor.fetchall()]


def checkin(conn, loan_id: int) -> None:
    loan_id = int(loan_id)
    today = date.today().isoformat()

    with db_transaction(conn):
        cursor = conn.cursor()
        row = cursor.execute(
            "SELECT Date_in FROM BOOK_LOANS WHERE Loan_id = ?",
            (loan_id,),
        ).fetchone()
        if not row:
            raise ValueError("Loan not found")
        if row["Date_in"] is not None:
            raise ValueError("Loan already closed")

        cursor.execute(
            "UPDATE BOOK_LOANS SET Date_in = ? WHERE Loan_id = ?",
            (today, loan_id),
        )

        # Import locally to avoid circular dependency during module import.
        from fines import refresh_fines

        refresh_fines(conn, loan_id=loan_id)
