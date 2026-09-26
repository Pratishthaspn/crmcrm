"""
=============================================================================
CRM - Database Management Module (database.py)
=============================================================================
This module handles:
1. Connecting to the local SQLite database ('smallbiz.db').
2. Setting up tables (Customers, Interactions, Follow-ups, Settings).
3. Seeding realistic sample business data for student viva demonstration.
4. Enabling Foreign Keys for data integrity.

Why SQLite for a College Mini Project?
- Serverless, zero-configuration: stored in a single '.db' file.
- Built right into Python standard library (`import sqlite3`).
- Easy for professors to inspect and students to explain.
=============================================================================
"""

import sqlite3
import os
from datetime import datetime, timedelta

# Database file path in the project directory
DB_NAME = "smallbiz.db"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), DB_NAME)


def get_db_connection():
    """
    Establishes and returns a connection to the SQLite database.
    - row_factory = sqlite3.Row allows column access by name (e.g., row['email'])
    - foreign_keys = ON ensures relational constraints (e.g., ON DELETE CASCADE)
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(seed_if_empty=True):
    """
    Creates tables if they don't already exist and optionally seeds sample data.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Customers Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS customers (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL,
        phone TEXT NOT NULL,
        company TEXT,
        address TEXT,
        status TEXT NOT NULL DEFAULT 'Active', -- 'Active', 'Inactive', 'Pending'
        notes TEXT,
        created_at TEXT NOT NULL,
        last_contact TEXT
    );
    """)

    # 2. Interactions Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS interactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        type TEXT NOT NULL,                   -- 'Call', 'Email', 'Meeting', 'WhatsApp', 'Other'
        description TEXT NOT NULL,
        interaction_date TEXT NOT NULL,
        follow_up_date TEXT,
        FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
    );
    """)

    # 3. Follow-ups Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS followups (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        customer_id INTEGER NOT NULL,
        reason TEXT NOT NULL,
        follow_up_date TEXT NOT NULL,
        priority TEXT NOT NULL DEFAULT 'Medium', -- 'Low', 'Medium', 'High'
        status TEXT NOT NULL DEFAULT 'Pending',   -- 'Pending', 'Completed'
        FOREIGN KEY (customer_id) REFERENCES customers (id) ON DELETE CASCADE
    );
    """)

    # 4. Settings Table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY CHECK (id = 1),
        business_name TEXT NOT NULL,
        owner_email TEXT NOT NULL,
        owner_phone TEXT NOT NULL,
        currency TEXT NOT NULL DEFAULT 'INR',
        theme TEXT NOT NULL DEFAULT 'light'
    );
    """)

    conn.commit()

    # Seed sample data if table is currently empty
    if seed_if_empty:
        cursor.execute("SELECT COUNT(*) AS count FROM customers;")
        count = cursor.fetchone()["count"]
        if count == 0:
            seed_sample_data(conn)

    conn.close()


def seed_sample_data(conn=None):
    """
    Populates the database with realistic sample customers, interactions, and follow-ups.
    Useful for demonstration during practical exams and college vivas.
    """
    should_close = False
    if conn is None:
        conn = get_db_connection()
        should_close = True

    cursor = conn.cursor()

    # Clear existing data cleanly if re-seeding
    cursor.execute("DELETE FROM followups;")
    cursor.execute("DELETE FROM interactions;")
    cursor.execute("DELETE FROM customers;")
    cursor.execute("DELETE FROM settings;")

    today = datetime.now()
    d = lambda days: (today - timedelta(days=days)).strftime("%Y-%m-%d")
    future_d = lambda days: (today + timedelta(days=days)).strftime("%Y-%m-%d")

    # Sample settings
    cursor.execute("""
    INSERT INTO settings (id, business_name, owner_email, owner_phone, currency, theme)
    VALUES (1, 'CRM Enterprises', 'support@crm.local', '+91 98765 00000', '₹', 'light');
    """)

    # 10 Sample Customers
    sample_customers = [
        (
            "Aarav Sharma",
            "aarav.sharma@example.com",
            "9876543210",
            "Sharma Electronics",
            "Shop 14, Lamington Road, Mumbai",
            "Active",
            "High-value regional distributor for consumer electronics. Buys quarterly.",
            d(45),
            d(2)
        ),
        (
            "Priya Patel",
            "priya.patel@example.com",
            "9823456789",
            "Patel Organic Grocers",
            "Near SG Highway, Ahmedabad",
            "Active",
            "Reliable monthly client. Interested in expanded organic grains catalogue.",
            d(60),
            d(4)
        ),
        (
            "Rohan Mehta",
            "rohan.mehta@example.com",
            "9712345678",
            "Mehta Logistics & Freight",
            "MIDC Phase II, Hinjewadi, Pune",
            "Pending",
            "Evaluating fleet maintenance contract. Demo quotation sent last week.",
            d(15),
            d(1)
        ),
        (
            "Ananya Iyer",
            "ananya.iyer@example.com",
            "9934567890",
            "Craftisan Handmade Decor",
            "12th Main, Indiranagar, Bengaluru",
            "Active",
            "Regular bulk buyer for festive corporate gifting packages.",
            d(90),
            d(5)
        ),
        (
            "Vikram Singh",
            "vikram.singh@example.com",
            "9654321098",
            "Singh Auto Components",
            "Mayapuri Industrial Area, New Delhi",
            "Inactive",
            "Account paused due to inventory restructuring. Follow up next quarter.",
            d(120),
            d(40)
        ),
        (
            "Neha Gupta",
            "neha.gupta@example.com",
            "9845123456",
            "BrightPath Edutech Solutions",
            "Hitec City, Madhapur, Hyderabad",
            "Active",
            "Procured software training licenses. Requested hardware quote.",
            d(30),
            d(3)
        ),
        (
            "Rajesh Verma",
            "rajesh.verma@example.com",
            "9765432109",
            "Verma Textile Mills",
            "Ring Road Market, Surat",
            "Pending",
            "Sample fabric batch dispatched. Awaiting final quality check approval.",
            d(10),
            d(2)
        ),
        (
            "Sneha Reddy",
            "sneha.reddy@example.com",
            "9987654321",
            "Reddy Culinary & Catering",
            "TTK Road, Alwarpet, Chennai",
            "Active",
            "Long-term client for commercial kitchen cutlery supplies.",
            d(75),
            d(6)
        ),
        (
            "Aditya Joshi",
            "aditya.joshi@example.com",
            "9811234567",
            "Zenith Creative Studio",
            "MI Road, C-Scheme, Jaipur",
            "Inactive",
            "Completed brand design project in January. Re-engage for marketing.",
            d(150),
            d(65)
        ),
        (
            "Kavita Nair",
            "kavita.nair@example.com",
            "9871122334",
            "Greenfield Solar Power",
            "Kaloor Stadium Link Rd, Kochi",
            "Active",
            "Rooftop solar panel maintenance partner. Very prompt payer.",
            d(20),
            d(3)
        )
    ]

    for cust in sample_customers:
        cursor.execute("""
        INSERT INTO customers (name, email, phone, company, address, status, notes, created_at, last_contact)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
        """, cust)

    # Fetch inserted customer IDs
    cursor.execute("SELECT id, name FROM customers ORDER BY id ASC;")
    cust_rows = cursor.fetchall()
    cid = {row["name"]: row["id"] for row in cust_rows}

    # Sample Interactions
    sample_interactions = [
        (cid["Aarav Sharma"], "Call", "Discussed quarterly bulk order for smart switches and relays. Sent updated rate sheet.", d(2), future_d(3)),
        (cid["Aarav Sharma"], "WhatsApp", "Shared revised PDF catalogue with festival wholesale discounts.", d(8), None),
        (cid["Priya Patel"], "Meeting", "In-person visit to retail outlet. Inspected cold storage inventory requirements.", d(4), future_d(5)),
        (cid["Priya Patel"], "Email", "Emailed formal invoice copy for Order #PO-8821.", d(12), None),
        (cid["Rohan Mehta"], "Call", "Introductory discovery call regarding logistics partnership and SLA terms.", d(1), future_d(2)),
        (cid["Rohan Mehta"], "Email", "Sent customized proposal presentation and rate card.", d(5), None),
        (cid["Ananya Iyer"], "WhatsApp", "Confirmed dispatch of 50 handmade ceramic showcase samples.", d(5), future_d(7)),
        (cid["Ananya Iyer"], "Call", "Client requested urgent dispatch for additional 20 units.", d(18), None),
        (cid["Vikram Singh"], "Call", "Status check on pending payments. Client requested 30 days extension.", d(40), None),
        (cid["Neha Gupta"], "Meeting", "Virtual demo with IT training team. They appreciated the reporting features.", d(3), future_d(4)),
        (cid["Neha Gupta"], "Email", "Sent security compliance documentation and license agreements.", d(9), None),
        (cid["Rajesh Verma"], "WhatsApp", "Courier tracking number shared for sample swatches.", d(2), future_d(1)),
        (cid["Sneha Reddy"], "Call", "Scheduled routine equipment servicing for next Tuesday.", d(6), future_d(6)),
        (cid["Aditya Joshi"], "Email", "Followed up regarding annual website maintenance renewal.", d(65), None),
        (cid["Kavita Nair"], "Meeting", "Site audit at Kochi solar farm. Signed annual maintenance contract.", d(3), future_d(8))
    ]

    for inter in sample_interactions:
        cursor.execute("""
        INSERT INTO interactions (customer_id, type, description, interaction_date, follow_up_date)
        VALUES (?, ?, ?, ?, ?);
        """, inter)

    # Sample Follow-ups
    sample_followups = [
        (cid["Rohan Mehta"], "Confirm decision on proposal and finalize contract signing", future_d(2), "High", "Pending"),
        (cid["Rajesh Verma"], "Get confirmation on sample fabric quality and initial order quantity", future_d(1), "High", "Pending"),
        (cid["Aarav Sharma"], "Follow up on bulk order purchase order (PO) generation", future_d(3), "Medium", "Pending"),
        (cid["Neha Gupta"], "Check if IT team reviewed the license agreement and security docs", future_d(4), "Medium", "Pending"),
        (cid["Priya Patel"], "Verify warehouse stock readiness for weekly organic dispatch", future_d(5), "Low", "Pending"),
        (cid["Sneha Reddy"], "Conduct scheduled routine maintenance on kitchen appliances", future_d(6), "Medium", "Pending"),
        (cid["Ananya Iyer"], "Confirm delivery receipt and client satisfaction with gift sets", future_d(7), "Low", "Pending"),
        (cid["Kavita Nair"], "Verify advance token payment cleared for solar site", future_d(8), "Medium", "Pending"),
        (cid["Aarav Sharma"], "Send product catalogue PDF on WhatsApp", d(8), "Low", "Completed"),
        (cid["Priya Patel"], "Resolve duplicate billing query", d(14), "High", "Completed"),
        (cid["Neha Gupta"], "Organize product walkthrough zoom call", d(10), "Medium", "Completed")
    ]

    for f in sample_followups:
        cursor.execute("""
        INSERT INTO followups (customer_id, reason, follow_up_date, priority, status)
        VALUES (?, ?, ?, ?, ?);
        """, f)

    conn.commit()
    if should_close:
        conn.close()


def reset_database():
    """Helper function to reset database back to initial sample state."""
    init_db(seed_if_empty=False)
    conn = get_db_connection()
    seed_sample_data(conn)
    conn.close()


if __name__ == "__main__":
    print(f"Initializing database at: {DB_PATH}")
    init_db()
    print("Database initialized and sample data seeded successfully!")
