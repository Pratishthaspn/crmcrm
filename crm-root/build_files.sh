#!/bin/bash
set -e

echo "Installing Python dependencies..."
python3 -m pip install -r requirements.txt

echo "Collecting static files..."
cd Django-CRM-main/src
python3 manage.py collectstatic --noinput --clear
