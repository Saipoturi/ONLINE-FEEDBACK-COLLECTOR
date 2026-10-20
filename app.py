"""
Online Feedback Collector with Admin Dashboard
Author: Antigravity Pair Programmer
Tech Stack: Python, Flask, SQLite, Jinja2, HTML5, CSS3, JavaScript
"""

import os
import re
import csv
import io
import sqlite3
import logging
import secrets
from datetime import datetime
from functools import wraps
from contextlib import contextmanager
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    flash,
    Response,
    jsonify,
    session
)

# Initialize Flask Application
app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'anti_gravity_feedback_super_secret_key_2026')

# Session security configuration
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE='Lax',
)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Admin Credentials (configurable via environment variables; fallback for local development)
DEFAULT_ADMIN_USER = 'admin'
DEFAULT_ADMIN_PASS = 'admin123'

# Database path (stored in the same directory as app.py)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE_PATH = os.path.join(BASE_DIR, 'database.db')


def get_db_connection():
    """Establish and return a connection to the SQLite database with Row factory."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


@contextmanager
def get_db():
    """Context manager for SQLite database connection to ensure automatic closing."""
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    """Automatically create the Feedback table if it does not already exist."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Feedback (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    email TEXT NOT NULL,
                    rating INTEGER NOT NULL CHECK (rating >= 1 AND rating <= 5),
                    comments TEXT NOT NULL,
                    date_submitted TEXT NOT NULL
                )
            ''')
            conn.commit()
            logging.info("Database initialized successfully.")
    except sqlite3.Error as e:
        logging.error("Failed to initialize database: %s", str(e))


# Initialize database when app module is loaded (preserves existing data)
init_db()


def validate_email(email_str):
    """Validate email format using standard regex."""
    if not email_str or len(email_str) > 254:
        return False
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email_str.strip()) is not None


def verify_admin_credentials(username, password):
    """Securely verify admin credentials using constant-time comparison."""
    if not username or not password:
        return False
    configured_user = os.environ.get('ADMIN_USERNAME', DEFAULT_ADMIN_USER)
    configured_pass = os.environ.get('ADMIN_PASSWORD', DEFAULT_ADMIN_PASS)

    user_matches = secrets.compare_digest(username.strip(), configured_user.strip())
    pass_matches = secrets.compare_digest(password, configured_pass)
    return user_matches and pass_matches


def admin_required(f):
    """Decorator to restrict access to authenticated administrators only."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash("Access restricted. Please sign in with administrator credentials.", "error")
            return redirect(url_for('admin_login', next=request.path))
        return f(*args, **kwargs)
    return decorated_function


@app.after_request
def add_security_headers(response):
    """Prevent browser caching on administrative routes to prevent access upon back-navigation after logout."""
    if request.path.startswith('/admin') or request.path.startswith('/export'):
        response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate, private"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
    return response


# ----------------------------------------------------------------------
# Public Routes (Accessible without login)
# ----------------------------------------------------------------------

@app.route('/')
def index():
    """Render the Public Home Page with the interactive Feedback Form."""
    return render_template('index.html')


@app.route('/submit-feedback', methods=['POST'])
def submit_feedback():
    """Receive, validate and save feedback into the SQLite database. Open to the public."""
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.is_json

    try:
        # Retrieve form data
        if request.is_json:
            data = request.get_json() or {}
            name = data.get('name', '').strip()
            email = data.get('email', '').strip()
            rating_raw = data.get('rating')
            comments = data.get('comments', '').strip()
        else:
            name = request.form.get('name', '').strip()
            email = request.form.get('email', '').strip()
            rating_raw = request.form.get('rating')
            comments = request.form.get('comments', '').strip()

        # Validation Checks
        errors = []

        if not name or len(name) < 2:
            errors.append("Please enter your name (at least 2 characters).")

        if not email or not validate_email(email):
            errors.append("Please provide a valid email address.")

        try:
            rating = int(rating_raw)
            if rating < 1 or rating > 5:
                errors.append("Rating must be an integer between 1 and 5.")
        except (ValueError, TypeError):
            errors.append("Please select a rating between 1 and 5.")
            rating = None

        if not comments or len(comments) < 5:
            errors.append("Please write your comments (at least 5 characters).")

        if errors:
            error_message = " ".join(errors)
            if is_ajax:
                return jsonify({"success": False, "message": error_message, "errors": errors}), 400
            flash(error_message, "error")
            return redirect(url_for('index'))

        # Prepare timestamp
        date_submitted = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Insert into database using parameterized query
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute(
                '''
                INSERT INTO Feedback (name, email, rating, comments, date_submitted)
                VALUES (?, ?, ?, ?, ?)
                ''',
                (name, email, rating, comments, date_submitted)
            )
            conn.commit()

        success_message = "Thank you! Your feedback has been submitted successfully."
        logging.info("Feedback received from %s (%s) with rating %s", name, email, rating)

        if is_ajax:
            return jsonify({
                "success": True,
                "message": success_message,
                "feedback": {
                    "name": name,
                    "email": email,
                    "rating": rating,
                    "date_submitted": date_submitted
                }
            }), 200

        flash(success_message, "success")
        return redirect(url_for('index'))

    except sqlite3.Error as db_err:
        logging.error("Database error occurred while submitting feedback: %s", str(db_err))
        user_err = "An internal error occurred while saving your feedback. Please try again later."
        if is_ajax:
            return jsonify({"success": False, "message": user_err}), 500
        flash(user_err, "error")
        return redirect(url_for('index'))

    except Exception as exc:
        logging.error("Unexpected error in /submit-feedback: %s", str(exc))
        user_err = "An unexpected error occurred. Please verify your input and try again."
        if is_ajax:
            return jsonify({"success": False, "message": user_err}), 500
        flash(user_err, "error")
        return redirect(url_for('index'))


# ----------------------------------------------------------------------
# Admin Authentication Routes
# ----------------------------------------------------------------------

@app.route('/admin-login', methods=['GET', 'POST'])
def admin_login():
    """Admin Login Portal."""
    # If already logged in, redirect directly to admin dashboard
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_dashboard'))

    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')

        if verify_admin_credentials(username, password):
            session.clear()
            session['admin_logged_in'] = True
            session['admin_user'] = username
            flash("Welcome back, Administrator! You have signed in successfully.", "success")

            next_url = request.args.get('next')
            if next_url and next_url.startswith('/'):
                return redirect(next_url)
            return redirect(url_for('admin_dashboard'))
        else:
            flash("Invalid administrator username or password. Please try again.", "error")
            return render_template('login.html', username=username), 401

    return render_template('login.html')


@app.route('/admin-logout', methods=['GET', 'POST'])
def admin_logout():
    """Log out administrator and clear session."""
    session.clear()
    flash("You have been signed out successfully.", "success")
    return redirect(url_for('admin_login'))


# ----------------------------------------------------------------------
# Protected Admin Dashboard & Management Routes
# ----------------------------------------------------------------------

@app.route('/admin-dashboard')
@admin_required
def admin_dashboard():
    """Display all submitted feedback and analytical metrics in the protected Admin Dashboard."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()

            # Fetch all feedback ordered by newest first
            cursor.execute('''
                SELECT id, name, email, rating, comments, date_submitted
                FROM Feedback
                ORDER BY id DESC
            ''')
            feedback_rows = cursor.fetchall()

            # Compute summary statistics
            total_feedback = len(feedback_rows)

            if total_feedback > 0:
                total_rating_sum = sum(row['rating'] for row in feedback_rows)
                avg_rating = round(total_rating_sum / total_feedback, 1)
            else:
                avg_rating = 0.0

            # Compute rating distribution (counts for 1 to 5 stars)
            rating_counts = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for row in feedback_rows:
                r = row['rating']
                if r in rating_counts:
                    rating_counts[r] += 1

            # Compute satisfaction rate (% of ratings with 4 or 5 stars)
            if total_feedback > 0:
                positive_ratings = rating_counts[4] + rating_counts[5]
                satisfaction_rate = round((positive_ratings / total_feedback) * 100, 1)
            else:
                satisfaction_rate = 0.0

        return render_template(
            'admin.html',
            feedback_list=feedback_rows,
            total_feedback=total_feedback,
            avg_rating=avg_rating,
            rating_counts=rating_counts,
            satisfaction_rate=satisfaction_rate
        )

    except sqlite3.Error as db_err:
        logging.error("Database error in /admin-dashboard: %s", str(db_err))
        flash("Unable to load feedback data at this time. Please try again.", "error")
        return render_template(
            'admin.html',
            feedback_list=[],
            total_feedback=0,
            avg_rating=0.0,
            rating_counts={1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
            satisfaction_rate=0.0
        )


@app.route('/export-csv')
@app.route('/export-feedback-csv')
@admin_required
def export_csv():
    """Export all feedback records as a downloadable CSV file. Protected by authentication."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id, name, email, rating, comments, date_submitted
                FROM Feedback
                ORDER BY id ASC
            ''')
            rows = cursor.fetchall()

        # Build in-memory CSV
        output = io.StringIO()
        writer = csv.writer(output)

        # Write CSV Header row
        writer.writerow(['ID', 'Name', 'Email', 'Rating (1-5)', 'Comments', 'Date Submitted'])

        # Write Data rows
        for row in rows:
            writer.writerow([
                row['id'],
                row['name'],
                row['email'],
                row['rating'],
                row['comments'],
                row['date_submitted']
            ])

        output.seek(0)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"feedback_export_{timestamp}.csv"

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": f"attachment; filename={filename}",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    except sqlite3.Error as db_err:
        logging.error("Database error during CSV export: %s", str(db_err))
        flash("Error exporting feedback data to CSV.", "error")
        return redirect(url_for('admin_dashboard'))


@app.route('/delete-feedback/<int:feedback_id>', methods=['POST'])
@admin_required
def delete_feedback(feedback_id):
    """Allow authenticated admin to remove a feedback entry."""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM Feedback WHERE id = ?', (feedback_id,))
            conn.commit()

        flash(f"Feedback entry #{feedback_id} was successfully deleted.", "success")
    except sqlite3.Error as db_err:
        logging.error("Failed to delete feedback #%s: %s", feedback_id, str(db_err))
        flash("Failed to delete the feedback entry.", "error")

    return redirect(url_for('admin_dashboard'))


# ----------------------------------------------------------------------
# Error Handlers
# ----------------------------------------------------------------------

@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 Not Found error gracefully."""
    return render_template('layout.html', custom_content="""
        <div class="empty-state" style="padding: 60px 20px; text-align: center;">
            <h1 style="font-size: 3rem; color: var(--primary);">404</h1>
            <h2>Page Not Found</h2>
            <p>The page you are looking for does not exist.</p>
            <a href="/" class="btn btn-primary" style="margin-top: 20px; display: inline-block;">Return Home</a>
        </div>
    """), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 Internal Server Error gracefully."""
    return render_template('layout.html', custom_content="""
        <div class="empty-state" style="padding: 60px 20px; text-align: center;">
            <h1 style="font-size: 3rem; color: var(--danger);">500</h1>
            <h2>Server Error</h2>
            <p>Something went wrong on our end. Please try again later.</p>
            <a href="/" class="btn btn-primary" style="margin-top: 20px; display: inline-block;">Return Home</a>
        </div>
    """), 500


if __name__ == '__main__':
    # Run the Flask development server on port 5000
    print("=" * 60)
    print("Online Feedback Collector & Protected Admin Portal")
    print("Public Feedback URL: http://127.0.0.1:5000")
    print("Admin Login Portal:  http://127.0.0.1:5000/admin-login")
    print("Admin Dashboard:     http://127.0.0.1:5000/admin-dashboard")
    print("Default Credentials: admin / admin123")
    print("=" * 60)
    app.run(debug=True, host='127.0.0.1', port=5000)
