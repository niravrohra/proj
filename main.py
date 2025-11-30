from db import get_connection
from load_data import load_all
from search import search_books
from loans import checkout, find_open_loans, checkin
from borrowers import create_borrower
from fines import refresh_fines, list_outstanding_fines, pay_fines


MENU = """
Library CLI
===========
1) Reload normalized CSV data
2) Search books
3) Checkout book
4) Find open loans
5) Checkin book
6) Create borrower
7) Show outstanding fines
8) Refresh fines
9) Pay fines
0) Quit
"""


def prompt(text: str) -> str:
    return input(text).strip()


def handle_reload(conn):
    confirm = prompt("This will drop all tables. Type 'yes' to continue: ")
    if confirm.lower() == "yes":
        load_all(conn)
        print("Database reloaded.")
    else:
        print("Reload cancelled.")


def handle_search(conn):
    query = prompt("Enter ISBN, title, or author search: ")
    results = search_books(conn, query)
    if not results:
        print("No matches found.")
        return
    for row in results:
        authors = row.get("Authors", "") or "Unknown"
        print(f"{row['Isbn']} | {row['Title']} | {authors} | {row['Status']}")


def handle_checkout(conn):
    isbn = prompt("ISBN: ")
    card = prompt("Card ID: ")
    try:
        loan_id = checkout(conn, isbn, int(card))
        print(f"Checkout complete. Loan ID: {loan_id}")
    except ValueError as err:
        print(f"Checkout failed: {err}")


def handle_find_loans(conn):
    search_type = prompt("Search loans by (i) ISBN, (c) Card ID, (n) Name: ").lower()
    kwargs = {}
    if search_type == "i":
        kwargs["isbn"] = prompt("ISBN: ")
    elif search_type == "c":
        card_val = prompt("Card ID: ")
        try:
            kwargs["card_id"] = int(card_val)
        except ValueError:
            print("Invalid card ID.")
            return
    elif search_type == "n":
        kwargs["borrower_name"] = prompt("Borrower name: ")
    else:
        print("Invalid choice")
        return
    try:
        loans = find_open_loans(conn, **kwargs)
    except ValueError as err:
        print(err)
        return
    if not loans:
        print("No open loans found.")
        return
    for loan in loans:
        print(
            f"Loan {loan['Loan_id']}: {loan['Isbn']} - {loan['Title']} | Card {loan['Card_id']} | Due {loan['Due_date']}"
        )


def handle_checkin(conn):
    loan_id = prompt("Loan ID to check in: ")
    try:
        checkin(conn, int(loan_id))
        print("Book checked in.")
    except ValueError as err:
        print(f"Checkin failed: {err}")


def handle_create_borrower(conn):
    ssn = prompt("SSN (xxx-xx-xxxx): ")
    name = prompt("Borrower name: ")
    address = prompt("Address: ")
    phone = prompt("Phone (optional): ")
    try:
        card_id = create_borrower(conn, ssn, name, address, phone)
        print(f"Borrower created with Card ID {card_id}")
    except ValueError as err:
        print(f"Could not create borrower: {err}")


def handle_show_fines(conn):
    fines = list_outstanding_fines(conn)
    if not fines:
        print("No unpaid fines.")
        return
    for fine in fines:
        print(f"Card {fine['Card_id']} | {fine['Bname']} | ${fine['Total_Fines']:.2f}")


def handle_refresh_fines(conn):
    refresh_fines(conn)
    print("Fines refreshed.")


def handle_pay_fines(conn):
    card_id = prompt("Card ID to pay fines for: ")
    try:
        pay_fines(conn, int(card_id))
        print("Fines marked as paid.")
    except ValueError as err:
        print(f"Payment failed: {err}")


def main():
    with get_connection() as conn:
        while True:
            print(MENU)
            choice = prompt("Select option: ")
            if choice == "1":
                handle_reload(conn)
            elif choice == "2":
                handle_search(conn)
            elif choice == "3":
                handle_checkout(conn)
            elif choice == "4":
                handle_find_loans(conn)
            elif choice == "5":
                handle_checkin(conn)
            elif choice == "6":
                handle_create_borrower(conn)
            elif choice == "7":
                handle_show_fines(conn)
            elif choice == "8":
                handle_refresh_fines(conn)
            elif choice == "9":
                handle_pay_fines(conn)
            elif choice == "0":
                print("Goodbye!")
                break
            else:
                print("Invalid option.")


if __name__ == "__main__":
    main()
