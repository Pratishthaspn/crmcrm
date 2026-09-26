"""
=============================================================================
CRM - Data Models & CRUD Operations (models.py)
=============================================================================
This file contains pure Python functions that interact with the SQLite database.
It handles all CRUD operations:
- C: Create (INSERT INTO ...)
- R: Read   (SELECT ... FROM ...)
- U: Update (UPDATE ... SET ...)
- D: Delete (DELETE FROM ...)

All queries use parameterized placeholders (`?`) to demonstrate best practices
and prevent SQL Injection attacks to examiners during viva.
=============================================================================
"""

from datetime import datetime
from database import get_db_connection


# ===========================================================================
# CUSTOMER CRUD OPERATIONS
# ===========================================================================

def get_customers(search_query=None, status_filter=None):
    """
    Retrieves all customers with optional search and status filtering.
    - search_query searches across Name, Email, Phone, and Company.
    - status_filter matches 'Active', 'Inactive', or 'Pending'.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM customers WHERE 1=1"
    params = []

    if status_filter and status_filter.lower() != 'all':
        query += " AND LOWER(status) = LOWER(?)"
        params.append(status_filter)

    if search_query:
        search_pattern = f"%{search_query.strip()}%"
        query += """ AND (
            name LIKE ? OR 
            email LIKE ? OR 
            phone LIKE ? OR 
            company LIKE ?
        )"""
        params.extend([search_pattern, search_pattern, search_pattern, search_pattern])

    query += " ORDER BY id DESC"
    cursor.execute(query, params)
    customers = cursor.fetchall()
    conn.close()
    return customers


def get_customer_by_id(customer_id):
    """Returns a single customer record by primary key, or None if not found."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM customers WHERE id = ?", (customer_id,))
    customer = cursor.fetchone()
    conn.close()
    return customer


def create_customer(name, email, phone, company, address, status="Active", notes=""):
    """
    Inserts a new customer into the database.
    Returns the newly generated primary key id.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    created_at = datetime.now().strftime("%Y-%m-%d")
    last_contact = created_at

    cursor.execute("""
        INSERT INTO customers (name, email, phone, company, address, status, notes, created_at, last_contact)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (name.strip(), email.strip(), phone.strip(), company.strip() if company else "",
          address.strip() if address else "", status, notes.strip() if notes else "",
          created_at, last_contact))

    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_customer(customer_id, name, email, phone, company, address, status, notes):
    """Updates existing customer attributes."""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE customers
        SET name = ?, email = ?, phone = ?, company = ?, address = ?, status = ?, notes = ?
        WHERE id = ?
    """, (name.strip(), email.strip(), phone.strip(), company.strip() if company else "",
          address.strip() if address else "", status, notes.strip() if notes else "",
          customer_id))

    conn.commit()
    conn.close()
    return True


def delete_customer(customer_id):
    """
    Deletes customer by ID.
    Because FOREIGN KEY constraints have ON DELETE CASCADE enabled,
    associated interactions and follow-ups are automatically removed.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()
    return True


# ===========================================================================
# INTERACTION CRUD OPERATIONS
# ===========================================================================

def get_interactions(type_filter=None, limit=None):
    """
    Fetches interactions joined with customer details.
    Allows filtering by type (Call, Email, Meeting, WhatsApp, Other).
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT i.*, c.name AS customer_name, c.company AS customer_company
        FROM interactions i
        JOIN customers c ON i.customer_id = c.id
        WHERE 1=1
    """
    params = []

    if type_filter and type_filter.lower() != 'all':
        query += " AND LOWER(i.type) = LOWER(?)"
        params.append(type_filter)

    query += " ORDER BY i.interaction_date DESC, i.id DESC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    interactions = cursor.fetchall()
    conn.close()
    return interactions


def get_customer_interactions(customer_id):
    """Fetches all interactions for a specific customer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM interactions
        WHERE customer_id = ?
        ORDER BY interaction_date DESC, id DESC
    """, (customer_id,))
    interactions = cursor.fetchall()
    conn.close()
    return interactions


def create_interaction(customer_id, interaction_type, description, interaction_date=None, follow_up_date=None):
    """
    Logs a new interaction and updates the customer's last_contact date.
    """
    if not interaction_date:
        interaction_date = datetime.now().strftime("%Y-%m-%d")

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Insert interaction
    cursor.execute("""
        INSERT INTO interactions (customer_id, type, description, interaction_date, follow_up_date)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, interaction_type, description.strip(), interaction_date, follow_up_date if follow_up_date else None))

    new_id = cursor.lastrowid

    # 2. Update customer last_contact date
    cursor.execute("""
        UPDATE customers
        SET last_contact = ?
        WHERE id = ?
    """, (interaction_date, customer_id))

    # 3. If a follow-up date was specified, optionally auto-create a pending follow-up
    if follow_up_date:
        cursor.execute("""
            INSERT INTO followups (customer_id, reason, follow_up_date, priority, status)
            VALUES (?, ?, ?, 'Medium', 'Pending')
        """, (customer_id, f"Follow-up for {interaction_type}: {description[:40]}...", follow_up_date))

    conn.commit()
    conn.close()
    return new_id


def delete_interaction(interaction_id):
    """Deletes an interaction log entry."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM interactions WHERE id = ?", (interaction_id,))
    conn.commit()
    conn.close()
    return True


# ===========================================================================
# FOLLOW-UP CRUD OPERATIONS
# ===========================================================================

def get_followups(status_filter=None, limit=None):
    """
    Fetches follow-up tasks joined with customer info.
    Sorts by follow_up_date ascending so urgent tasks come first.
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT f.*, c.name AS customer_name, c.company AS customer_company, c.phone AS customer_phone
        FROM followups f
        JOIN customers c ON f.customer_id = c.id
        WHERE 1=1
    """
    params = []

    if status_filter and status_filter.lower() != 'all':
        query += " AND LOWER(f.status) = LOWER(?)"
        params.append(status_filter)

    query += " ORDER BY f.status DESC, f.follow_up_date ASC"

    if limit:
        query += " LIMIT ?"
        params.append(limit)

    cursor.execute(query, params)
    followups = cursor.fetchall()
    conn.close()
    return followups


def get_customer_followups(customer_id):
    """Fetches follow-up reminders for a single customer."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT * FROM followups
        WHERE customer_id = ?
        ORDER BY follow_up_date ASC
    """, (customer_id,))
    followups = cursor.fetchall()
    conn.close()
    return followups

# Helper alias for alternate naming
get_followups_by_customer_id = get_customer_followups
get_interactions_by_customer_id = get_customer_interactions



def get_followup_by_id(followup_id):
    """Retrieves a single follow-up task by ID."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT f.*, c.name AS customer_name
        FROM followups f
        JOIN customers c ON f.customer_id = c.id
        WHERE f.id = ?
    """, (followup_id,))
    followup = cursor.fetchone()
    conn.close()
    return followup


def create_followup(customer_id, reason, follow_up_date, priority="Medium", status="Pending"):
    """Creates a new follow-up task."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO followups (customer_id, reason, follow_up_date, priority, status)
        VALUES (?, ?, ?, ?, ?)
    """, (customer_id, reason.strip(), follow_up_date, priority, status))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()
    return new_id


def update_followup(followup_id, reason, follow_up_date, priority, status):
    """Updates an existing follow-up."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        UPDATE followups
        SET reason = ?, follow_up_date = ?, priority = ?, status = ?
        WHERE id = ?
    """, (reason.strip(), follow_up_date, priority, status, followup_id))
    conn.commit()
    conn.close()
    return True


def toggle_followup_status(followup_id):
    """Toggles follow-up between 'Pending' and 'Completed'."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT status FROM followups WHERE id = ?", (followup_id,))
    row = cursor.fetchone()
    if row:
        new_status = "Pending" if row["status"] == "Completed" else "Completed"
        cursor.execute("UPDATE followups SET status = ? WHERE id = ?", (new_status, followup_id))
        conn.commit()
        conn.close()
        return new_status
    conn.close()
    return None


def delete_followup(followup_id):
    """Deletes a follow-up item."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM followups WHERE id = ?", (followup_id,))
    conn.commit()
    conn.close()
    return True


# ===========================================================================
# DASHBOARD & REPORTS METRICS
# ===========================================================================

def get_dashboard_data():
    """
    Computes key summary cards and gathers recent activity for the main dashboard:
    1. Total Customers
    2. Active Customers
    3. Pending Follow-ups
    4. Total Interactions
    Plus:
    - 5 Recent Customers
    - 5 Recent Interactions
    - 5 Upcoming Pending Follow-ups
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Metric 1: Total Customers
    cursor.execute("SELECT COUNT(*) AS count FROM customers;")
    total_customers = cursor.fetchone()["count"]

    # Metric 2: Active Customers
    cursor.execute("SELECT COUNT(*) AS count FROM customers WHERE status = 'Active';")
    active_customers = cursor.fetchone()["count"]

    # Metric 3: Pending Follow-ups
    cursor.execute("SELECT COUNT(*) AS count FROM followups WHERE status = 'Pending';")
    pending_followups = cursor.fetchone()["count"]

    # Metric 4: Total Interactions
    cursor.execute("SELECT COUNT(*) AS count FROM interactions;")
    total_interactions = cursor.fetchone()["count"]

    # Recent 5 Customers
    cursor.execute("SELECT * FROM customers ORDER BY id DESC LIMIT 5;")
    recent_customers = cursor.fetchall()

    # Recent 5 Interactions with customer name
    cursor.execute("""
        SELECT i.*, c.name AS customer_name
        FROM interactions i
        JOIN customers c ON i.customer_id = c.id
        ORDER BY i.interaction_date DESC, i.id DESC
        LIMIT 5;
    """)
    recent_interactions = cursor.fetchall()

    # Upcoming 5 Pending Follow-ups
    cursor.execute("""
        SELECT f.*, c.name AS customer_name, c.company AS customer_company
        FROM followups f
        JOIN customers c ON f.customer_id = c.id
        WHERE f.status = 'Pending'
        ORDER BY f.follow_up_date ASC
        LIMIT 5;
    """)
    upcoming_followups = cursor.fetchall()

    conn.close()

    return {
        "total_customers": total_customers,
        "active_customers": active_customers,
        "pending_followups": pending_followups,
        "total_interactions": total_interactions,
        "recent_customers": recent_customers,
        "recent_interactions": recent_interactions,
        "upcoming_followups": upcoming_followups
    }


def get_reports_data():
    """
    Aggregates statistical distribution data for charts on the Reports page:
    1. Customers by Status (Active, Inactive, Pending)
    2. Interactions by Type (Call, Email, Meeting, WhatsApp, Other)
    3. Follow-ups by Status (Pending, Completed)
    4. Follow-ups by Priority (High, Medium, Low)
    5. Key numbers: Total Customers, New This Month, Completed Follow-ups, Interactions
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Customers by status
    cursor.execute("""
        SELECT status, COUNT(*) AS count 
        FROM customers 
        GROUP BY status;
    """)
    status_rows = cursor.fetchall()
    customer_status_data = {"Active": 0, "Inactive": 0, "Pending": 0}
    for row in status_rows:
        customer_status_data[row["status"]] = row["count"]

    # 2. Interactions by type
    cursor.execute("""
        SELECT type, COUNT(*) AS count 
        FROM interactions 
        GROUP BY type;
    """)
    type_rows = cursor.fetchall()
    interaction_type_data = {"Call": 0, "Email": 0, "Meeting": 0, "WhatsApp": 0, "Other": 0}
    for row in type_rows:
        interaction_type_data[row["type"]] = row["count"]

    # 3. Follow-ups by status
    cursor.execute("""
        SELECT status, COUNT(*) AS count 
        FROM followups 
        GROUP BY status;
    """)
    fu_status_rows = cursor.fetchall()
    followup_status_data = {"Pending": 0, "Completed": 0}
    for row in fu_status_rows:
        followup_status_data[row["status"]] = row["count"]

    # 4. Follow-ups by priority
    cursor.execute("""
        SELECT priority, COUNT(*) AS count 
        FROM followups 
        GROUP BY priority;
    """)
    priority_rows = cursor.fetchall()
    priority_data = {"High": 0, "Medium": 0, "Low": 0}
    for row in priority_rows:
        priority_data[row["priority"]] = row["count"]

    # 5. New Customers This Month
    current_month_prefix = datetime.now().strftime("%Y-%m")
    cursor.execute("SELECT COUNT(*) AS count FROM customers WHERE created_at LIKE ?;", (f"{current_month_prefix}%",))
    new_this_month = cursor.fetchone()["count"]

    # 6. Overall totals
    cursor.execute("SELECT COUNT(*) AS count FROM customers;")
    total_customers = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM interactions;")
    total_interactions = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) AS count FROM followups WHERE status = 'Completed';")
    completed_followups = cursor.fetchone()["count"]

    conn.close()

    return {
        "customer_status": customer_status_data,
        "interaction_types": interaction_type_data,
        "followup_status": followup_status_data,
        "followup_priority": priority_data,
        "total_customers": total_customers,
        "new_this_month": new_this_month,
        "completed_followups": completed_followups,
        "total_interactions": total_interactions
    }


# ===========================================================================
# SETTINGS
# ===========================================================================

def get_settings():
    """Retrieves business profile settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM settings WHERE id = 1;")
    settings = cursor.fetchone()
    conn.close()
    if not settings:
        return {
            "business_name": "CRM",
            "owner_email": "admin@crm.local",
            "owner_phone": "+91 98765 43210",
            "currency": "₹",
            "theme": "light"
        }
    return settings


def update_settings(business_name, owner_email, owner_phone, currency="₹", theme="light"):
    """Updates business profile settings."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO settings (id, business_name, owner_email, owner_phone, currency, theme)
        VALUES (1, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            business_name = excluded.business_name,
            owner_email = excluded.owner_email,
            owner_phone = excluded.owner_phone,
            currency = excluded.currency,
            theme = excluded.theme;
    """, (business_name.strip(), owner_email.strip(), owner_phone.strip(), currency.strip(), theme))
    conn.commit()
    conn.close()
    return True
