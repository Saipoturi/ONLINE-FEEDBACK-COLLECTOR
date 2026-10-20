# Online Feedback Collector

## About
A web application that collects user feedback and helps the admin analyze ratings and comments.

## Features
- Submit feedback with name, email, rating, and comments.
- Admin login and dashboard.
- View feedback statistics and ratings.
- Export feedback data as a CSV file.

## Technologies Used
- Frontend: HTML, CSS, JavaScript
- Backend: Python Flask
- Database: SQLite

## How to Run
1. Install the required packages:
   ```bash
   pip install -r requirements.txt
   ```
2. Run the application:
   ```bash
   python app.py
   ```
3. Open `http://127.0.0.1:5000` in your browser.

## Admin Login
Open `http://127.0.0.1:5000/admin-login` and log in using your configured admin credentials.

## Project Structure
- `app.py` – Backend application
- `templates/` – HTML pages
- `static/` – CSS and JavaScript files
- `database.db` – SQLite database
- `requirements.txt` – Required Python packages
