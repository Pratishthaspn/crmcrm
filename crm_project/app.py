"""
=============================================================================
CRM - Main Application Entrypoint (app.py)
=============================================================================
A clean, student-friendly Customer Relationship Management (CRM) web application
built for a Python Programming College Mini Project.

Features:
- Customer Directory (Full CRUD: Create, Read, Update, Delete)
- Search and Filtering (by Name, Company, Email, Phone, Status)
- Interaction History Logging (Calls, Meetings, Emails, WhatsApp)
- Follow-up Reminders & One-Click Status Toggling
- Interactive Analytical Visualizations & Key Business KPIs
- Clean modular structure with Flask and built-in SQLite3
- Complete 16-file downloadable ZIP package export

How to Run:
1. python app.py
2. Open your web browser at: http://127.0.0.1:5000/
=============================================================================
"""

import os
from flask import Flask
from database import init_db
from routes import crm_bp

def create_app():
    """Application factory for CRM."""
    app = Flask(__name__)
    
    # Secret key used for session signing and flash messages
    app.secret_key = os.environ.get("SECRET_KEY", "crm-college-project-secret-2026")

    # Initialize the SQLite database and seed initial demo records
    with app.app_context():
        init_db()

    # Register the main Blueprint containing all CRM routes
    app.register_blueprint(crm_bp)

    # Custom Jinja template filters for clean formatting in HTML
    @app.template_filter("badge_color")
    def badge_color_filter(status):
        """Returns CSS badge class based on status or priority."""
        status_map = {
            "active": "badge-active",
            "inactive": "badge-inactive",
            "pending": "badge-pending",
            "completed": "badge-completed",
            "high": "badge-high",
            "medium": "badge-medium",
            "low": "badge-low"
        }
        return status_map.get(str(status).lower(), "badge-default")

    @app.template_filter("initials")
    def initials_filter(name):
        """Extracts first letter of first and last name for avatar badges."""
        if not name:
            return "CR"
        parts = name.strip().split()
        if len(parts) >= 2:
            return f"{parts[0][0]}{parts[-1][0]}".upper()
        return name[:2].upper()

    return app


app = create_app()

if __name__ == "__main__":
    print("=" * 65)
    print(" 🚀 Starting CRM - College Python Mini Project")
    print(" 🌐 Access Dashboard at: http://127.0.0.1:5000/")
    print(" 📂 Database: smallbiz.db (SQLite3)")
    print("=" * 65)
    app.run(debug=True, host="127.0.0.1", port=5000)
