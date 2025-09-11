#!/bin/bash

# Exit on error
set -e

# Database configuration
DB_NAME="nature_quest"
DB_USER="nature_quest_user"
DB_PASSWORD="nature_quest_password"

# Create the database user
sudo -u postgres psql -c "CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';" || echo "User $DB_USER already exists, continuing..."

# Create the database
sudo -u postgres createdb -O $DB_USER $DB_NAME || echo "Database $DB_NAME already exists, continuing..."

# Enable PostGIS extension
sudo -u postgres psql -d $DB_NAME -c "CREATE EXTENSION IF NOT EXISTS postgis;"

echo "Database setup complete!"
echo "Update your .env file with the following database settings:"
echo "POSTGRES_DB=$DB_NAME"
echo "POSTGRES_USER=$DB_USER"
echo "POSTGRES_PASSWORD=$DB_PASSWORD"
echo "POSTGRES_HOST=localhost"
echo "POSTGRES_PORT=5432"
