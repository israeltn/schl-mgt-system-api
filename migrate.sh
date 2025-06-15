#!/bin/bash

# Migration script for School Management System

echo "Running migrations for School Management System..."

# Make migrations for all apps
echo "Creating migrations..."
python manage.py makemigrations accounts
python manage.py makemigrations schools
python manage.py makemigrations academics
python manage.py makemigrations students
python manage.py makemigrations results
python manage.py makemigrations financials

# Apply migrations
echo "Applying migrations..."
python manage.py migrate

echo "Migrations completed!"

# Optional: Create superuser
read -p "Do you want to create a superuser? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]
then
    python manage.py createsuperuser
fi