from datetime import date
from typing import List, Optional

from db import db_transaction

DAILY_FINE = 0.25


def _parse_iso(value: str) -> date:
    return date.fromisoformat(value)


def refresh_fines(conn, today: Optional[date] = None, loan_id: Optional[int] = None) -> None:
    today = today or date.today()
    params = {"today": today.isoformat()}
    extra_clause = ""
    if loan_id is not None:
        extra_clause = " AND Loan_id = :loan_id"
        params["loan_id"] = int(loan_id)

    cursor = conn.cursor()
    rows = cursor.execute(
        """
        SELECT Loan_id, Due_date, Date_in
        FROM BOOK_LOANS
        WHERE Due_date < :today
          AND (Date_in IS NULL OR Date_in > Due_date)
        """
        + extra_clause,
        params,
    ).fetchall()

    with db_transaction(conn):
        for row in rows:
            due_date = _parse_iso(row["Due_date"])
            if row["Date_in"]:
                end_date = _parse_iso(row["Date_in"])
            else:
                end_date = today
            days_late = (end_date - due_date).days
            if days_late <= 0:
                continue
            fine_amt = round(days_late * DAILY_FINE, 2)

            existing = conn.execute(
                "SELECT Paid FROM FINES WHERE Loan_id = ?",
                (row["Loan_id"],),
            ).fetchone()
            if existing:
                if existing["Paid"]:
                    continue
                conn.execute(
                    "UPDATE FINES SET Fine_amt = ? WHERE Loan_id = ? AND Paid = 0",
                    (fine_amt, row["Loan_id"]),
                )
            else:
                conn.execute(
                    "INSERT INTO FINES (Loan_id, Fine_amt, Paid) VALUES (?, ?, 0)",
                    (row["Loan_id"], fine_amt),
                )


def list_outstanding_fines(conn) -> List[dict]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            bor.Card_id,
            bor.Bname,
            SUM(f.Fine_amt) AS Total_Fines
        FROM FINES f
        JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
        JOIN BORROWER bor  ON bl.Card_id = bor.Card_id
        WHERE f.Paid = 0
        GROUP BY bor.Card_id, bor.Bname
        ORDER BY bor.Bname
        """
    )
    return [dict(row) for row in cursor.fetchall()]


def pay_fines(conn, card_id: int) -> None:
    card_id = int(card_id)
    with db_transaction(conn):
        open_loans = conn.execute(
            """
            SELECT COUNT(*)
            FROM FINES f
            JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
            WHERE bl.Card_id = ? AND f.Paid = 0 AND bl.Date_in IS NULL
            """,
            (card_id,),
        ).fetchone()[0]
        if open_loans:
            raise ValueError("Borrower still has books checked out")

        updated = conn.execute(
            """
            UPDATE FINES
            SET Paid = 1
            WHERE Loan_id IN (
                SELECT f.Loan_id
                FROM FINES f
                JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
                WHERE bl.Card_id = ? AND f.Paid = 0
            )
            """,
            (card_id,),
        )
        if updated.rowcount == 0:
            raise ValueError("No unpaid fines for this borrower")
