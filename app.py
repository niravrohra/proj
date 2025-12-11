from flask import Flask, render_template, request, redirect, url_for, flash, session
from functools import wraps
from db import get_connection
import search
import loans
import borrowers
import fines
import auth

app = Flask(__name__)
app.secret_key = 'library_secret_key_change_in_production'  # Change this in production!

# Initialize default admin user on startup
with get_connection() as conn:
    auth.initialize_default_user(conn)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            flash('Please log in to access this page.', 'error')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        with get_connection() as conn:
            if auth.verify_user(conn, username, password):
                session['logged_in'] = True
                session['username'] = username
                flash('Login successful!', 'success')
                return redirect(url_for('index'))
            else:
                flash('Invalid username or password.', 'error')
    
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirm_password')
        ssn = request.form.get('ssn')
        full_name = request.form.get('full_name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        if password != confirm_password:
            flash('Passwords do not match.', 'error')
        elif not ssn or not full_name or not address:
            flash('SSN, full name, and address are required.', 'error')
        else:
            try:
                with get_connection() as conn:
                    # Create borrower account with user-provided SSN
                    card_id = borrowers.create_borrower(conn, ssn, full_name, address, phone)
                    
                    # Create user account linked to borrower
                    auth.create_user(conn, username, password, card_id=card_id)
                    
                    flash(f'Account created successfully! Your Borrower Card ID is: {card_id}', 'success')
                    return redirect(url_for('login'))
            except ValueError as e:
                flash(str(e), 'error')
            except Exception as e:
                flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('register.html')

@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('login'))

@app.route('/profile')
@login_required
def profile():
    username = session.get('username')
    
    with get_connection() as conn:
        # Get user info
        user_info = auth.get_user_info(conn, username)
        
        # Get active loans if user has a card_id
        active_loans = []
        outstanding_fines = []
        total_fines = 0
        
        if user_info and user_info['Card_id']:
            card_id = user_info['Card_id']
            
            # Get active loans
            try:
                active_loans = loans.find_open_loans(conn, card_id=card_id)
            except:
                pass
            
            # Get fines
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    f.Loan_id,
                    f.Fine_amt,
                    bl.Isbn,
                    b.Title,
                    bl.Due_date
                FROM FINES f
                JOIN BOOK_LOANS bl ON f.Loan_id = bl.Loan_id
                JOIN BOOK b ON bl.Isbn = b.Isbn
                WHERE bl.Card_id = ? AND f.Paid = 0
            """, (card_id,))
            outstanding_fines = [dict(row) for row in cursor.fetchall()]
            total_fines = sum(f['Fine_amt'] for f in outstanding_fines)
    
    return render_template('profile.html', 
                         user=user_info, 
                         loans=active_loans,
                         fines=outstanding_fines,
                         total_fines=total_fines)

@app.route('/profile/link-borrower', methods=['POST'])
@login_required
def link_borrower():
    card_id = request.form.get('card_id')
    username = session.get('username')
    
    if not card_id:
        flash('Card ID is required.', 'error')
        return redirect(url_for('profile'))
    
    try:
        card_id = int(card_id)
        
        with get_connection() as conn:
            # Check if borrower exists
            borrower = conn.execute(
                "SELECT Card_id, Bname FROM BORROWER WHERE Card_id = ?",
                (card_id,)
            ).fetchone()
            
            if not borrower:
                flash(f'Borrower with Card ID {card_id} not found.', 'error')
                return redirect(url_for('profile'))
            
            # Check if this borrower is already linked to another user
            existing_user = conn.execute(
                "SELECT Username FROM USERS WHERE Card_id = ? AND Username != ?",
                (card_id, username)
            ).fetchone()
            
            if existing_user:
                flash(f'This borrower account is already linked to another user.', 'error')
                return redirect(url_for('profile'))
            
            # Link borrower to current user
            conn.execute(
                "UPDATE USERS SET Card_id = ? WHERE Username = ?",
                (card_id, username)
            )
            conn.commit()
            
            flash(f'Successfully linked to borrower account: {borrower["Bname"]} (Card ID: {card_id})', 'success')
    except ValueError:
        flash('Invalid Card ID format.', 'error')
    except Exception as e:
        flash(f'Error linking borrower: {str(e)}', 'error')
    
    return redirect(url_for('profile'))

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/search', methods=['GET'])
@login_required
def search_books():
    query = request.args.get('q', '')
    page = int(request.args.get('page', 1))
    status_filter = request.args.get('status', 'all')  # all, available, checked_out
    per_page = 50
    offset = (page - 1) * per_page
    
    results = []
    total_count = 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Build WHERE clause based on filters
        where_conditions = []
        params = []
        
        if query:
            # Search in ISBN, Title, or Author
            where_conditions.append("(LOWER(b.Isbn) LIKE ? OR LOWER(b.Title) LIKE ? OR LOWER(a.Name) LIKE ?)")
            search_term = f"%{query.lower()}%"
            params.extend([search_term, search_term, search_term])
        
        # Status filter
        if status_filter == 'available':
            where_conditions.append("NOT EXISTS (SELECT 1 FROM BOOK_LOANS bl WHERE bl.Isbn = b.Isbn AND bl.Date_in IS NULL)")
        elif status_filter == 'checked_out':
            where_conditions.append("EXISTS (SELECT 1 FROM BOOK_LOANS bl WHERE bl.Isbn = b.Isbn AND bl.Date_in IS NULL)")
        
        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""
        
        # Get total count for pagination
        count_query = f"""
            SELECT COUNT(DISTINCT b.Isbn)
            FROM BOOK b
            LEFT JOIN BOOK_AUTHORS ba ON b.Isbn = ba.Isbn
            LEFT JOIN AUTHORS a ON ba.Author_id = a.Author_id
            {where_clause}
        """
        total_count = cursor.execute(count_query, params).fetchone()[0]
        
        # Get paginated results
        results_query = f"""
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
            {where_clause}
            GROUP BY b.Isbn, b.Title
            ORDER BY b.Title
            LIMIT ? OFFSET ?
        """
        cursor.execute(results_query, params + [per_page, offset])
        results = [dict(row) for row in cursor.fetchall()]
    
    total_pages = (total_count + per_page - 1) // per_page
    
    return render_template('search.html', 
                         results=results, 
                         query=query,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         status_filter=status_filter)

@app.route('/loans', methods=['GET', 'POST'])
@login_required
def view_loans():
    # Helper to checkin
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'checkin':
            loan_ids = request.form.getlist('loan_id')
            if loan_ids:
                try:
                    # Convert strings to ints
                    ids = [int(x) for x in loan_ids]
                    with get_connection() as conn:
                        loans.checkin_multiple(conn, ids)
                    flash(f"Successfully checked in {len(loan_ids)} book(s).", "success")
                except Exception as e:
                    flash(str(e), "error")
        return redirect(url_for('view_loans'))

    # GET request - Search for loans to checkin or view
    search_term = request.args.get('q', '')
    search_type = request.args.get('type', 'borrower_name')
    open_loans = []
    
    if search_term:
        with get_connection() as conn:
            try:
                if search_type == 'card_id':
                     open_loans = loans.find_open_loans(conn, card_id=search_term)
                elif search_type == 'isbn':
                     open_loans = loans.find_open_loans(conn, isbn=search_term)
                else:
                     open_loans = loans.find_open_loans(conn, borrower_name=search_term)
            except ValueError:
                pass # No filter or invalid filter

    return render_template('loans.html', loans=open_loans, search_term=search_term, search_type=search_type)

@app.route('/checkout', methods=['POST'])
@login_required
def checkout_book():
    isbn = request.form.get('isbn')
    card_id = request.form.get('card_id')
    
    if not isbn or not card_id:
        flash("ISBN and Card ID are required.", "error")
        return redirect(url_for('view_loans'))

    try:
        with get_connection() as conn:
            loans.checkout(conn, isbn, card_id)
        flash(f"Book {isbn} checked out to Card {card_id}.", "success")
    except Exception as e:
        flash(str(e), "error")
    
    return redirect(url_for('view_loans'))

@app.route('/borrowers', methods=['GET', 'POST'])
@login_required
def manage_borrowers():
    if request.method == 'POST':
        ssn = request.form.get('ssn')
        name = request.form.get('name')
        address = request.form.get('address')
        phone = request.form.get('phone')
        
        try:
            with get_connection() as conn:
                new_id = borrowers.create_borrower(conn, ssn, name, address, phone)
            flash(f"Borrower created successfully! Card ID: {new_id}", "success")
            return redirect(url_for('manage_borrowers'))
        except Exception as e:
            flash(str(e), "error")
    
    # Pagination
    page = int(request.args.get('page', 1))
    per_page = 50
    offset = (page - 1) * per_page
    
    # Get all borrowers with pagination
    all_borrowers = []
    total_count = 0
    
    with get_connection() as conn:
        cursor = conn.cursor()
        
        # Get total count
        total_count = cursor.execute("SELECT COUNT(*) FROM BORROWER").fetchone()[0]
        
        # Get paginated results
        cursor.execute("""
            SELECT Card_id, Ssn, Bname, Address, Phone
            FROM BORROWER
            ORDER BY Card_id DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        all_borrowers = [dict(row) for row in cursor.fetchall()]
    
    total_pages = (total_count + per_page - 1) // per_page
    
    # Get current user's card_id
    user_card_id = None
    username = session.get('username')
    with get_connection() as conn:
        row = conn.execute("SELECT Card_id FROM USERS WHERE Username = ?", (username,)).fetchone()
        if row:
            user_card_id = row[0]

    return render_template('borrowers.html', 
                         borrowers=all_borrowers,
                         page=page,
                         total_pages=total_pages,
                         total_count=total_count,
                         user_card_id=user_card_id)

@app.route('/borrowers/delete/<int:card_id>', methods=['POST'])
@login_required
def delete_borrower(card_id):
    try:
        username = session.get('username')
        
        with get_connection() as conn:
            # Check if this borrower belongs to the current user
            user_card_id = conn.execute(
                "SELECT Card_id FROM USERS WHERE Username = ?",
                (username,)
            ).fetchone()
            
            if user_card_id and user_card_id[0] == card_id:
                flash("You cannot delete your own borrower account.", "error")
                return redirect(url_for('manage_borrowers'))
            
            # Check if borrower has active loans
            active_loans = conn.execute(
                "SELECT COUNT(*) FROM BOOK_LOANS WHERE Card_id = ? AND Date_in IS NULL",
                (card_id,)
            ).fetchone()[0]
            
            if active_loans > 0:
                flash(f"Cannot delete borrower: {active_loans} active loan(s) exist.", "error")
            else:
                # Unlink any users linked to this borrower
                conn.execute("UPDATE USERS SET Card_id = NULL WHERE Card_id = ?", (card_id,))
                
                # Delete borrower
                conn.execute("DELETE FROM BORROWER WHERE Card_id = ?", (card_id,))
                conn.commit()
                flash(f"Borrower {card_id} deleted successfully.", "success")
    except Exception as e:
        flash(f"Error deleting borrower: {str(e)}", "error")
    
    return redirect(url_for('manage_borrowers'))

@app.route('/profile/unlink-borrower', methods=['POST'])
@login_required
def unlink_borrower():
    """Manually unlink a broken borrower account"""
    username = session.get('username')
    
    try:
        with get_connection() as conn:
            conn.execute("UPDATE USERS SET Card_id = NULL WHERE Username = ?", (username,))
            conn.commit()
            flash("Borrower account unlinked successfully. You can now link a new account.", "success")
    except Exception as e:
        flash(f"Error unlinking borrower: {str(e)}", "error")
    
    return redirect(url_for('profile'))

@app.route('/fines', methods=['GET', 'POST'])
@login_required
def manage_fines():
    # Handle fine payment or refresh
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'refresh':
            with get_connection() as conn:
                fines.refresh_fines(conn)
            flash("Fines refreshed successfully.", "success")
        elif action == 'pay':
            card_id = request.form.get('card_id')
            try:
                with get_connection() as conn:
                    fines.pay_fines(conn, card_id)
                flash(f"Fines paid for Card ID {card_id}.", "success")
            except Exception as e:
                flash(str(e), "error")
        return redirect(url_for('manage_fines'))

    # List outstanding fines
    outstanding = []
    with get_connection() as conn:
        outstanding = fines.list_outstanding_fines(conn)
    
    return render_template('fines.html', fines=outstanding)

if __name__ == '__main__':
    app.run(debug=True)
