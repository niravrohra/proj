# Library Database (Milestone 2)

This repository contains the tooling for Milestone 2 of the CS 4347 database project. It assumes the four normalized CSV files created by `normalize.py` are available in the project root:

- `book.csv`
- `authors.csv`
- `book_authors.csv`
- `borrower.csv`

Run the normalization script if these files ever need to be regenerated:

```bash
python3 normalize.py
```

## Loading the database

`load_data.py` drops and recreates all tables defined in `schema.sql`, then bulk-loads the normalized CSVs into `library.db`.

```bash
python3 load_data.py
```

## CLI host application

`main.py` exposes all Milestone 2 functionality from a text menu:

1. Reload normalized CSV data
2. Search books across ISBN, title, and author (with availability indicator)
3. Checkout a book with loan validation rules
4. Find open loans for ISBN, borrower card ID, or borrower name
5. Check in a loan (automatically updating fines)
6. Create a borrower account with SSN uniqueness enforcement
7. Show outstanding fines grouped by borrower
8. Refresh fines for overdue loans
9. Pay fines once all books have been returned

```bash
python3 main.py
```

The CLI uses the shared helpers in `db.py`, `search.py`, `loans.py`, `borrowers.py`, and `fines.py` so that future Milestones can import the same logic from another interface.
