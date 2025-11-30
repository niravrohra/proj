from typing import List

SEARCH_BASE = """
SELECT
    b.Isbn,
    b.Title,
    COALESCE(GROUP_CONCAT(a.Name, ', '), '') AS Authors,
    CASE
        WHEN EXISTS (
            SELECT 1 FROM BOOK_LOANS bl WHERE bl.Isbn = b.Isbn AND bl.Date_in IS NULL
        ) THEN 'OUT'
        ELSE 'IN'
    END AS Status
FROM BOOK b
LEFT JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn
LEFT JOIN AUTHORS a ON ba.Author_id = a.Author_id
"""

TAIL = " GROUP BY b.Isbn, b.Title ORDER BY b.Title"


def search_books(conn, query: str) -> List[dict]:
    query = (query or "").strip()
    if not query:
        return []

    cursor = conn.cursor()
    if len(query) == 10 and query.isalnum():
        sql = SEARCH_BASE + " WHERE b.Isbn = ?" + TAIL
        cursor.execute(sql, (query,))
    else:
        term = f"%{query.lower()}%"
        sql = (
            SEARCH_BASE
            + " WHERE LOWER(b.Isbn) LIKE ? OR LOWER(b.Title) LIKE ? OR LOWER(a.Name) LIKE ?"
            + TAIL
        )
        cursor.execute(sql, (term, term, term))

    return [dict(row) for row in cursor.fetchall()]
