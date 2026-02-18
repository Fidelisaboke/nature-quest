#!/bin/bash

# Exit on error and undefined variables
set -euo pipefail

# Function to prompt for sensitive input
prompt_sensitive() {
    local prompt="$1"
    local var_name="$2"
    local input
    
    while true; do
        read -r -s -p "${prompt}: " input
        echo >&2  # Move to a new line
        if [ -n "$input" ]; then
            eval "$var_name=\$input"
# Enable PostGIS extension (owned by the DB owner)
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB_NAME" -c "CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;"
sudo -u postgres psql -v ON_ERROR_STOP=1 -d "$DB_NAME" -c "ALTER EXTENSION postgis OWNER TO \"$DB_USER\";"
        fi
    done
}

# Get database configuration from environment or prompt
if [ -z "${DB_NAME:-}" ]; then
    read -r -p "Enter database name [nature_quest]: " DB_NAME
    DB_NAME=${DB_NAME:-nature_quest}
fi

if [ -z "${DB_USER:-}" ]; then
    read -r -p "Enter database user [nature_quest_user]: " DB_USER
    DB_USER=${DB_USER:-nature_quest_user}
fi

if [ -z "${DB_PASSWORD:-}" ]; then
    prompt_sensitive "Enter database password (input hidden)" DB_PASSWORD
fi

# Validate inputs
if [ -z "$DB_NAME" ] || [ -z "$DB_USER" ] || [ -z "$DB_PASSWORD" ]; then
    echo "Error: Database name, user, and password are required" >&2
    exit 1
fi

# Create the database user
echo "Creating database user '$DB_USER'..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '$DB_USER') THEN
        CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD';
        RAISE NOTICE 'User $DB_USER created.';
    ELSE
        RAISE NOTICE 'User $DB_USER already exists, skipping...';
    END IF;
END
\$\$"

# Create the database
echo "Creating database '$DB_NAME'..."
sudo -u postgres psql -v ON_ERROR_STOP=1 -c "SELECT 'CREATE DATABASE $DB_NAME WITH OWNER = $DB_USER ENCODING = ''UTF8'''
    WHERE NOT EXISTS (SELECT FROM pg_database WHERE datname = '$DB_NAME')\gexec"

# Enable PostGIS extension
echo "Enabling PostGIS extension..."
sudo -u postgres psql -d "$DB_NAME" -v ON_ERROR_STOP=1 -c "CREATE EXTENSION IF NOT EXISTS postgis;"

# Create .env file if it doesn't exist
ENV_FILE="${ENV_FILE:-.env}"
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating $ENV_FILE with database configuration..."
    cat > "$ENV_FILE" << EOF
# Database configuration
POSTGRES_DB=$DB_NAME
POSTGRES_USER=$DB_USER
POSTGRES_PASSWORD=$DB_PASSWORD
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

# Other configuration
DJANGO_SECRET_KEY=$(openssl rand -hex 32)
DJANGO_DEBUG=True
DJANGO_ALLOWED_HOSTS=localhost,127.0.0.1

# Uncomment and configure as needed
# CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
# CSRF_TRUSTED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
EOF
    
    echo "\n$ENV_FILE created with database configuration and a new SECRET_KEY."
    echo "Please review and adjust other settings as needed."
else
    echo "\n$ENV_FILE already exists. Please ensure it contains the following database settings:"
    echo "POSTGRES_DB=$DB_NAME"
    echo "POSTGRES_USER=$DB_USER"
    echo "POSTGRES_PASSWORD=******"  # Don't show the actual password
    echo "POSTGRES_HOST=localhost"
    echo "POSTGRES_PORT=5432"
fi

echo "\nDatabase setup complete!"
