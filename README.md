# 📚 Books4U - Library Management System

A modern, full-featured library management system built with Flask, featuring user authentication, role-based access control, book search, loan management, borrower tracking, and fine calculation.

## ✨ Features

### 🔐 User Authentication & Authorization
- Secure login/logout with session management
- **Role-based access control** with three user types:
  - **Librarian**: Full access to all library management functions (cannot override restrictions)
  - **Borrower**: Access to personal account and book search (default for new registrations)
  - **Superuser**: Librarian privileges + ability to override checkout restrictions
- User registration with automatic borrower account creation (creates "borrower" role)
- Password hashing using Werkzeug
- Link existing borrower accounts to user profiles
- Default admin account (username: `admin`, password: `admin`) with superuser privileges

### 📖 Book Management
- **Advanced search** with 5-column results table:
  - ISBN
  - Title
  - Authors (comma-separated list)
  - Checked Out status (IN/OUT)
  - Borrower ID (shows who has the book if checked out)
- Search 25,000+ books by ISBN, title, or author (case-insensitive, substring matching)
- **Multiple book selection** for bulk checkout operations
- Pagination (50 books per page)
- Filter by availability status (All, Available, Checked Out)
- Real-time availability tracking

### 👥 Borrower Management
- Create and manage borrower accounts
- View all borrowers with pagination
- Delete borrowers (with validation)
- Automatic SSN validation (one card per borrower)
- Automatic Card ID generation

### 📚 Loan Management
- Check out books to borrowers (by ISBN or from search results)
- **Bulk checkout**: Select multiple books and checkout with one action
- Search active loans by borrower name, card ID, or ISBN
- Bulk check-in functionality
- Due date tracking (14-day loan period)
- **Checkout restrictions** (can be overridden by superusers):
  - Maximum 3 active loans per borrower
  - No checkout if borrower has unpaid fines
  - No checkout if book is already checked out

### 💰 Fine Management
- Automatic fine calculation ($0.25 per day for overdue books)
- View outstanding fines grouped by borrower
- **Filter to show/hide paid fines**
- Pay fines (full amount only, requires all books returned)
- Refresh fines on-demand
- Fine calculation for:
  - Returned books: based on days between due_date and date_in
  - Still checked out: based on days between due_date and today

### 👤 User Profile & Borrower Homepage
- **Borrower Homepage**: Dedicated dashboard for borrowers showing:
  - Active loans with due dates
  - Outstanding fines summary
  - Quick book search access
- View personal borrower information
- Track active loans
- Monitor outstanding fines
- Link/unlink borrower accounts

### ⚡ Super-User Features (Bonus)
- **Override checkout restrictions**:
  - Can checkout books even if borrower has 3+ active loans
  - Can checkout books even if borrower has unpaid fines
  - Cannot override: book already checked out (still enforced)
- Visual indicators (⚡) throughout the interface
- Superuser badge in navigation menu

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Installation (macOS/Linux)

1. **Navigate to project directory**
   ```bash
   cd /path/to/CS-4347-Project
   ```

2. **Install dependencies**
   ```bash
   pip3 install -r requirements.txt
   ```
   Or if you have both Python 2 and 3:
   ```bash
   python3 -m pip install -r requirements.txt
   ```

3. **Initialize the database**
   ```bash
   python3 load_data.py
   ```
   This will create the database and load initial data (25,001 books, 15,549 authors, 1,000 borrowers).

4. **Start the application**
   ```bash
   python3 app.py
   ```

5. **Access the application**
   - Open your browser to: http://127.0.0.1:5000
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin`
     - Role: `superuser` (can override checkout restrictions)

### Installation (Windows)

1. **Navigate to project directory**
   ```powershell
   cd path\to\CS-4347-Project
   ```

2. **Run the setup script** (recommended)
   ```powershell
   .\setup.ps1
   ```
   
   The setup script will:
   - Check Python installation
   - Install Flask and Werkzeug
   - Create/reload the database
   - Offer to start the application

3. **Or manual setup**
   ```powershell
   # Install dependencies
   py -m pip install -r requirements.txt

   # Initialize database
   py load_data.py

   # Start the application
   py app.py
   ```

4. **Access the application**
   - Open your browser to: http://127.0.0.1:5000
   - Login with default credentials:
     - Username: `admin`
     - Password: `admin`

## 📁 Project Structure

```
CS-4347-Project/
├── app.py                 # Main Flask application (routes, role-based access)
├── auth.py                # User authentication & role management
├── borrowers.py           # Borrower management
├── loans.py               # Loan management (with override support)
├── fines.py               # Fine calculation & payment
├── search.py              # Book search functionality
├── db.py                  # Database utilities
├── load_data.py           # Database initialization
├── schema.sql             # Database schema (includes USERS table with Role)
├── requirements.txt       # Python dependencies (Flask, Werkzeug)
├── setup.ps1              # Automated setup script (Windows)
├── main.py                # CLI interface (optional)
├── static/
│   └── style.css          # Application styling
└── templates/
    ├── layout.html        # Base template (role-based navigation)
    ├── login.html         # Login page
    ├── register.html      # Registration page
    ├── index.html         # Home page (librarian dashboard)
    ├── borrower_homepage.html  # Borrower dashboard (NEW)
    ├── profile.html       # User profile
    ├── search.html        # Book search (with bulk selection)
    ├── loans.html         # Loan management
    ├── borrowers.html     # Borrower management
    └── fines.html         # Fine management (with paid/unpaid filter)
```

## 🎨 Design

- **Color Scheme**: Black, gray, and deep orange with deep red accents
- **Modern UI**: Glassmorphism effects, smooth animations, responsive design
- **Typography**: Inter font family for clean, professional look
- **Accessibility**: High contrast, clear labels, semantic HTML

## 🗄️ Database

The system uses SQLite with the following tables:
- **BOOK**: 25,001 books with ISBN, title
- **AUTHORS**: 15,549 authors
- **BOOK_AUTHORS**: Book-author relationships
- **BORROWER**: 1,000 borrowers with SSN, name, address, phone
- **BOOK_LOANS**: Loan records with dates and due dates
- **FINES**: Fine records linked to loans
- **USERS**: User accounts with authentication and roles (librarian, borrower, superuser)

## 🔒 Security Features

- Password hashing with Werkzeug
- Session-based authentication
- Protected routes with `@login_required` decorator
- Role-based access control with `@librarian_required` decorator
- CSRF protection via Flask sessions
- Input validation on all forms
- SQL injection prevention via parameterized queries

## 📝 Usage Guide

### User Roles

**Librarian**:
- Full access to all library management functions
- Can search books, manage loans, borrowers, and fines
- Cannot override checkout restrictions
- Can be created manually or by database administrators

**Borrower** (default for new registrations):
- Access to personal borrower homepage
- Can view their own loans and fines
- Can search books
- Cannot access librarian functions
- New accounts created through registration default to this role

**Superuser** (admin account):
- All librarian privileges
- Can override checkout restrictions:
  - Checkout books even if borrower has 3+ active loans
  - Checkout books even if borrower has unpaid fines
- Visual indicators (⚡) shown throughout interface
- Default admin account has this role

### Creating a New Account
1. Click "Create Account" on login page
2. Fill in username, password, SSN, name, and address
3. A borrower account is automatically created and linked
4. New accounts created through registration default to "borrower" role

### Searching for Books
1. Navigate to "Search" tab (available to all users)
2. Enter ISBN, title, or author name (case-insensitive, substring matching)
3. Filter by availability status (All, Available, Checked Out)
4. Use pagination to browse results (50 books per page)
5. **Bulk Selection**: Check multiple books and use "Checkout Selected Books" button
6. Results show 5 columns: ISBN, Title, Authors, Checked Out status, Borrower ID

### Checking Out Books

**Method 1: From Search Results**
1. Search for books
2. Click "Checkout" button on available books, OR
3. Select multiple books using checkboxes
4. Click "Checkout Selected Books" button
5. Enter Borrower Card ID when prompted

**Method 2: Direct Checkout**
1. Go to "Loans" tab (librarians only)
2. Enter ISBN and Card ID
3. Click "Check Out Title"
4. System validates:
   - Book exists and is available
   - Borrower exists
   - Borrower has < 3 active loans (unless superuser)
   - Borrower has no unpaid fines (unless superuser)

### Checking In Books
1. Go to "Loans" tab
2. Search for loans by:
   - Borrower name (substring matching)
   - Card ID
   - ISBN
3. Select one or more loans using checkboxes
4. Click "Check In Selected"
5. System automatically calculates fines for overdue books

### Managing Borrowers
1. Navigate to "Borrowers" tab (librarians only)
2. Create new borrowers:
   - Enter SSN (must be unique), name, address (required)
   - Phone is optional
   - Card ID is automatically generated
3. View all borrowers with pagination
4. Delete borrowers (only if no active loans)

### Viewing and Paying Fines
1. Go to "Fines" tab (librarians only)
2. Click "Refresh Fines" to calculate overdue fines ($0.25/day)
3. View outstanding fines grouped by borrower
4. Toggle "Show All Fines" to see paid and unpaid fines
5. Click "Pay Full Amount" to pay all fines for a borrower
   - Requires all books to be returned first
   - Cannot pay partial amounts

### Borrower Homepage
1. Borrowers are automatically redirected to their homepage
2. View active loans with due dates
3. View outstanding fines summary
4. Quick access to book search
5. Access profile to link/unlink borrower accounts

## 🛠️ Development

### Running in Debug Mode
The application runs in debug mode by default for development:
```python
if __name__ == '__main__':
    app.run(debug=True)
```

### Database Reset
To reset the database with fresh data:
```bash
# macOS/Linux
python3 load_data.py

# Windows
py load_data.py
```

### Creating Superuser Accounts
To create additional superuser accounts, you can:
1. Register a new account normally
2. Manually update the database:
   ```sql
   UPDATE USERS SET Role = 'superuser' WHERE Username = 'your_username';
   ```
Or modify `auth.py` to add a function for this.

### Port Configuration
If port 5000 is already in use, modify the last line in `app.py`:
```python
app.run(debug=True, port=5001)  # Use different port
```

## 🎯 Project Requirements Compliance

### Core Requirements ✅
- ✅ GUI interface (Flask web application)
- ✅ Book search with 5 columns (ISBN, Title, Authors, Checked Out, Borrower ID)
- ✅ Book checkout with all restrictions enforced
- ✅ Book check-in functionality
- ✅ Borrower management with SSN validation
- ✅ Fine calculation and payment system

### Bonus Features ✅ (Extra Credit)
- ✅ Login system with multiple accounts
- ✅ Role-based permissions (librarian, borrower, superuser)
- ✅ Multiple book selection for bulk checkout
- ✅ Borrower homepage for account management
- ✅ Super-user functions to override restrictions

## 🐛 Troubleshooting

### Port Already in Use
If you get "Address already in use" error:
- Stop other processes using port 5000, or
- Change the port in `app.py`: `app.run(debug=True, port=5001)`

### Database Errors
If you encounter database errors:
- Delete `library.db` and run `python3 load_data.py` again
- Ensure all CSV files are in the project directory

### Import Errors
If you get "Module not found" errors:
- Ensure you're in the project directory
- Run `pip3 install -r requirements.txt` again
- Use `python3` instead of `python` if you have both versions

## 📄 License

This project is for educational purposes as part of CS 4347 - Database Systems.

## 👥 Credits

Developed for CS 4347 - Database Systems

### Features Implemented
- All core functional requirements
- All bonus features for extra credit
- Role-based access control
- Modern, responsive UI
- Comprehensive error handling
