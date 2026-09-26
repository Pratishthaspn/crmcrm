"""
=============================================================================
CRM - Application Routes & Controller (routes.py)
=============================================================================
This module defines the Flask Blueprint for all application URL routes:
- Dashboard route
- Customer management routes (List, Add, View, Edit, Delete)
- Interaction tracking routes (List, Add, Delete)
- Follow-up management routes (List, Add, Edit, Toggle, Delete)
- Analytics & Reports route
- Settings & Sample Data Reset routes
- Project ZIP download routes for easy submission & evaluation

Demonstrates standard HTTP verbs (GET, POST), form handling, input validation,
flash messages, and Jinja2 template rendering for college viva examinations.
=============================================================================
"""

import io
import os
import re
import zipfile
from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, send_file, abort
import models
from database import reset_database

# Create Flask Blueprint for modular routing
crm_bp = Blueprint("crm", __name__)


def validate_customer_form(name, email, phone):
    """
    Validates mandatory customer fields:
    - Name must not be blank
    - Email must contain basic email structure (@ and domain)
    - Phone must contain valid digits (at least 7 digits)
    """
    if not name or len(name.strip()) < 2:
        return "Customer full name is required (minimum 2 characters)."
    
    # Basic email format validation
    email_pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    if not email or not re.match(email_pattern, email.strip()):
        return "Please enter a valid email address (e.g., name@example.com)."
    
    # Clean phone digits check
    digits = re.sub(r"\D", "", phone or "")
    if len(digits) < 7:
        return "Please enter a valid phone number (at least 7 digits)."
        
    return None


# ---------------------------------------------------------------------------
# DASHBOARD ROUTE
# ---------------------------------------------------------------------------
@crm_bp.route("/")
def home():
    """Root redirect to the main dashboard."""
    return redirect(url_for("crm.dashboard"))


@crm_bp.route("/dashboard")
def dashboard():
    """
    Renders main dashboard with 4 KPI summary cards,
    recent customer list, recent interactions, and pending follow-ups.
    """
    data = models.get_dashboard_data()
    settings = models.get_settings()
    return render_template(
        "dashboard.html",
        active_page="dashboard",
        data=data,
        settings=settings
    )


# ---------------------------------------------------------------------------
# CUSTOMERS ROUTES (CRUD)
# ---------------------------------------------------------------------------
@crm_bp.route("/customers")
def customers_list():
    """
    Displays the customer directory.
    Supports query parameters:
      - ?search=<keyword>
      - ?status=All|Active|Inactive|Pending
    """
    search_query = request.args.get("search", "").strip()
    status_filter = request.args.get("status", "All").strip()

    customers = models.get_customers(search_query, status_filter)
    settings = models.get_settings()

    return render_template(
        "customers.html",
        active_page="customers",
        customers=customers,
        search_query=search_query,
        status_filter=status_filter,
        settings=settings
    )


@crm_bp.route("/customers/add", methods=["POST"])
def customer_add():
    """Handles adding a new customer with input validation."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    company = request.form.get("company", "").strip()
    address = request.form.get("address", "").strip()
    status = request.form.get("status", "Active")
    notes = request.form.get("notes", "").strip()

    error = validate_customer_form(name, email, phone)
    if error:
        flash(error, "danger")
        return redirect(url_for("crm.customers_list"))

    new_id = models.create_customer(name, email, phone, company, address, status, notes)
    flash(f"Customer '{name}' added successfully! (ID: #CUST-{new_id})", "success")
    return redirect(url_for("crm.customers_list"))


@crm_bp.route("/customers/<int:customer_id>")
def customer_details(customer_id):
    """
    Displays full details for a selected customer,
    including their interaction history log and pending follow-ups.
    """
    customer = models.get_customer_by_id(customer_id)
    if not customer:
        flash(f"Customer ID #{customer_id} was not found.", "warning")
        return redirect(url_for("crm.customers_list"))

    interactions = models.get_customer_interactions(customer_id)
    followups = models.get_customer_followups(customer_id)
    settings = models.get_settings()

    return render_template(
        "customer_details.html",
        active_page="customers",
        customer=customer,
        interactions=interactions,
        followups=followups,
        settings=settings
    )


@crm_bp.route("/customers/edit/<int:customer_id>", methods=["POST"])
def customer_edit(customer_id):
    """Updates customer details."""
    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip()
    phone = request.form.get("phone", "").strip()
    company = request.form.get("company", "").strip()
    address = request.form.get("address", "").strip()
    status = request.form.get("status", "Active")
    notes = request.form.get("notes", "").strip()

    error = validate_customer_form(name, email, phone)
    if error:
        flash(error, "danger")
        return redirect(request.referrer or url_for("crm.customer_details", customer_id=customer_id))

    models.update_customer(customer_id, name, email, phone, company, address, status, notes)
    flash(f"Customer details for '{name}' updated successfully.", "success")
    return redirect(request.referrer or url_for("crm.customer_details", customer_id=customer_id))


@crm_bp.route("/customers/delete/<int:customer_id>", methods=["POST"])
def customer_delete(customer_id):
    """Deletes customer and cascading interactions/follow-ups."""
    cust = models.get_customer_by_id(customer_id)
    cust_name = cust["name"] if cust else f"#{customer_id}"
    models.delete_customer(customer_id)
    flash(f"Customer '{cust_name}' deleted.", "info")
    return redirect(url_for("crm.customers_list"))


# ---------------------------------------------------------------------------
# INTERACTIONS ROUTES
# ---------------------------------------------------------------------------
@crm_bp.route("/interactions")
def interactions_list():
    """
    Displays all customer interactions.
    Supports filtering by interaction type: Call, Email, Meeting, WhatsApp, Other.
    """
    type_filter = request.args.get("type", "All").strip()
    interactions = models.get_interactions(type_filter)
    customers = models.get_customers()  # For the Add Interaction customer dropdown
    settings = models.get_settings()

    return render_template(
        "interactions.html",
        active_page="interactions",
        interactions=interactions,
        type_filter=type_filter,
        customers=customers,
        settings=settings
    )


@crm_bp.route("/interactions/add", methods=["POST"])
def interaction_add():
    """Logs a new interaction."""
    customer_id = request.form.get("customer_id")
    interaction_type = request.form.get("type", "Call")
    description = request.form.get("description", "").strip()
    interaction_date = request.form.get("interaction_date")
    follow_up_date = request.form.get("follow_up_date") or None

    if not customer_id:
        flash("Please select a valid customer.", "danger")
        return redirect(request.referrer or url_for("crm.interactions_list"))

    if not description:
        flash("Please provide brief notes/description for the interaction.", "danger")
        return redirect(request.referrer or url_for("crm.interactions_list"))

    models.create_interaction(
        customer_id=int(customer_id),
        interaction_type=interaction_type,
        description=description,
        interaction_date=interaction_date,
        follow_up_date=follow_up_date
    )
    flash("Interaction logged successfully.", "success")
    return redirect(request.referrer or url_for("crm.interactions_list"))


@crm_bp.route("/interactions/delete/<int:interaction_id>", methods=["POST"])
def interaction_delete(interaction_id):
    """Deletes an interaction log entry."""
    models.delete_interaction(interaction_id)
    flash("Interaction deleted.", "info")
    return redirect(request.referrer or url_for("crm.interactions_list"))


# ---------------------------------------------------------------------------
# FOLLOW-UPS ROUTES
# ---------------------------------------------------------------------------
@crm_bp.route("/followups")
def followups_list():
    """
    Displays follow-up tasks.
    Supports filtering by status: All, Pending, Completed.
    """
    status_filter = request.args.get("status", "All").strip()
    followups = models.get_followups(status_filter)
    customers = models.get_customers()
    settings = models.get_settings()

    return render_template(
        "followups.html",
        active_page="followups",
        followups=followups,
        status_filter=status_filter,
        customers=customers,
        settings=settings
    )


@crm_bp.route("/followups/add", methods=["POST"])
def followup_add():
    """Creates a new follow-up task."""
    customer_id = request.form.get("customer_id")
    reason = request.form.get("reason", "").strip()
    follow_up_date = request.form.get("follow_up_date")
    priority = request.form.get("priority", "Medium")

    if not customer_id:
        flash("Please select a customer for this follow-up.", "danger")
        return redirect(request.referrer or url_for("crm.followups_list"))

    if not reason:
        flash("Follow-up reason cannot be empty.", "danger")
        return redirect(request.referrer or url_for("crm.followups_list"))

    if not follow_up_date:
        flash("Please select a scheduled follow-up date.", "danger")
        return redirect(request.referrer or url_for("crm.followups_list"))

    models.create_followup(int(customer_id), reason, follow_up_date, priority, status="Pending")
    flash("Follow-up task scheduled successfully.", "success")
    return redirect(request.referrer or url_for("crm.followups_list"))


@crm_bp.route("/followups/edit/<int:followup_id>", methods=["POST"])
def followup_edit(followup_id):
    """Edits follow-up details."""
    reason = request.form.get("reason", "").strip()
    follow_up_date = request.form.get("follow_up_date")
    priority = request.form.get("priority", "Medium")
    status = request.form.get("status", "Pending")

    if not reason or not follow_up_date:
        flash("Reason and date are required.", "danger")
        return redirect(request.referrer or url_for("crm.followups_list"))

    models.update_followup(followup_id, reason, follow_up_date, priority, status)
    flash("Follow-up updated successfully.", "success")
    return redirect(request.referrer or url_for("crm.followups_list"))


@crm_bp.route("/followups/toggle/<int:followup_id>", methods=["POST"])
def followup_toggle(followup_id):
    """
    Toggles follow-up between 'Pending' and 'Completed'.
    Quick one-click action for students during project viva.
    """
    new_status = models.toggle_followup_status(followup_id)
    if new_status:
        flash(f"Follow-up marked as {new_status}!", "success")
    return redirect(request.referrer or url_for("crm.followups_list"))


@crm_bp.route("/followups/delete/<int:followup_id>", methods=["POST"])
def followup_delete(followup_id):
    """Deletes a follow-up item."""
    models.delete_followup(followup_id)
    flash("Follow-up deleted.", "info")
    return redirect(request.referrer or url_for("crm.followups_list"))


# ---------------------------------------------------------------------------
# REPORTS & ANALYTICS
# ---------------------------------------------------------------------------
@crm_bp.route("/reports")
def reports():
    """
    Renders analytics and visual charts for:
    - Customer distribution by status
    - Interaction frequency by type
    - Follow-ups by status and priority
    """
    reports_data = models.get_reports_data()
    settings = models.get_settings()

    return render_template(
        "reports.html",
        active_page="reports",
        reports=reports_data,
        settings=settings
    )


@crm_bp.route("/api/reports-data")
def api_reports_data():
    """API endpoint returning JSON reports data for chart rendering."""
    return jsonify(models.get_reports_data())


# ---------------------------------------------------------------------------
# SETTINGS & DEMO CONTROLS
# ---------------------------------------------------------------------------
@crm_bp.route("/settings", methods=["GET", "POST"])
def settings_page():
    """Manages simple business profile and demonstration data reset."""
    if request.method == "POST":
        business_name = request.form.get("business_name", "CRM")
        owner_email = request.form.get("owner_email", "admin@crm.local")
        owner_phone = request.form.get("owner_phone", "+91 98765 43210")
        currency = request.form.get("currency", "₹")
        theme = request.form.get("theme", "light")

        models.update_settings(business_name, owner_email, owner_phone, currency, theme)
        flash("Settings saved successfully.", "success")
        return redirect(url_for("crm.settings_page"))

    current_settings = models.get_settings()
    return render_template(
        "settings.html",
        active_page="settings",
        settings=current_settings
    )


@crm_bp.route("/reset-database", methods=["POST"])
def reset_db_action():
    """
    Special helper route for college demonstrations:
    Resets the database back to clean sample customer and interaction records.
    """
    reset_database()
    flash("Database successfully reset to initial realistic sample data!", "info")
    return redirect(url_for("crm.dashboard"))


# ---------------------------------------------------------------------------
# DOWNLOADABLE PROJECT EXPORT (All 16 Files as ZIP or Individual Files)
# ---------------------------------------------------------------------------
# The exact 16 project files specified for this college mini project
PROJECT_16_FILES = [
    "app.py",
    "database.py",
    "models.py",
    "routes.py",
    "requirements.txt",
    "README.md",
    os.path.join("templates", "base.html"),
    os.path.join("templates", "dashboard.html"),
    os.path.join("templates", "customers.html"),
    os.path.join("templates", "customer_details.html"),
    os.path.join("templates", "followups.html"),
    os.path.join("templates", "interactions.html"),
    os.path.join("templates", "reports.html"),
    os.path.join("templates", "settings.html"),
    os.path.join("static", "css", "style.css"),
    os.path.join("static", "js", "script.js"),
]


@crm_bp.route("/download-project-zip")
@crm_bp.route("/download-zip")
def download_project_zip():
    """
    Dynamically packages all 16 clean project files into a single downloadable
    'CRM_Python_Project.zip' file for college submission and viva evaluation.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    zip_buffer = io.BytesIO()

    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for rel_path in PROJECT_16_FILES:
            full_path = os.path.join(base_dir, rel_path)
            if os.path.exists(full_path):
                # Standardize forward slashes inside ZIP
                arcname = "crm_project/" + rel_path.replace("\\", "/")
                zf.write(full_path, arcname=arcname)

    zip_buffer.seek(0)
    return send_file(
        zip_buffer,
        mimetype="application/zip",
        as_attachment=True,
        download_name="CRM_Python_Project.zip"
    )


@crm_bp.route("/download-file/<path:filepath>")
def download_single_file(filepath):
    """
    Allows downloading any of the 16 project source files individually.
    """
    base_dir = os.path.dirname(os.path.abspath(__file__))
    # Normalize path separators
    normalized_path = filepath.replace("/", os.sep).replace("\\", os.sep)

    # Security check: ensure requested file is in allowlist of 16 project files
    if normalized_path not in PROJECT_16_FILES:
        abort(404)

    full_path = os.path.join(base_dir, normalized_path)
    if not os.path.exists(full_path):
        abort(404)

    filename = os.path.basename(full_path)
    return send_file(full_path, as_attachment=True, download_name=filename)

