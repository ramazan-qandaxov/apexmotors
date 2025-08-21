#!/bin/bash

# Wait for the PostgreSQL database to become available
echo "⏳ Waiting for PostgreSQL..."

while ! nc -z db 5432; do
  sleep 1
done

echo "PostgreSQL is up!"

# Apply database migrations
echo "Applying database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Start Gunicorn server
echo "Starting Gunicorn..."
exec gunicorn apexmotors.wsgi:application --bind 0.0.0.0:8000
