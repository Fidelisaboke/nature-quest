#!/bin/bash
set -euo pipefail


# =============================================================================
# Nature Quest - PostgreSQL Database Setup Script
# =============================================================================
NC='\033[0m'        
GREEN='\033[0;32m'   
YELLOW='\033[1;33m' 
BLUE='\033[0;34m'    
RED='\033[0;31m'    

log() {
    echo -e "${BLUE}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

error() {
    echo -e "${RED}[ERROR] $1${NC}" >&2
}

success() {
    echo -e "${GREEN}[SUCCESS] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[WARNING] $1${NC}"
}


# =============================================================================
# PostgreSQL Database Setup Script
# =============================================================================

run_psql_super() {
    local sql="$1"
    local db="${2:-postgres}"
    # Prefer non-interactive sudo; fall back to password only if explicitly allowed.
    if [ -z "${POSTGRES_ADMIN_PASSWORD:-}" ]; then
        # Try non-interactive sudo first
        if sudo -n -u postgres psql -v ON_ERROR_STOP=1 -d "$db" -c "$sql" 2>/dev/null; then
            return 0
        fi
        # Only use the default “postgres” password if explicitly opted in
        if [ "${POSTGRES_ASSUME_DEFAULT_PASSWORD:-false}" = "true" ]; then
            PGPASSWORD="postgres" psql \
              -U postgres \
              -h "$POSTGRES_HOST" \
              -p "$POSTGRES_PORT" \
              -d "$db" \
              -v ON_ERROR_STOP=1 \
              -c "$sql"
        else
            return 1
        fi
    else
        PGPASSWORD="$POSTGRES_ADMIN_PASSWORD" psql \
          -U postgres \
          -h "$POSTGRES_HOST" \
          -p "$POSTGRES_PORT" \
          -d "$db" \
          -v ON_ERROR_STOP=1 \
          -c "$sql"
    fi
}


run_psql_db() {
    PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c "$1"
}

# =============================================================================
# ENVIRONMENT SETUP
# =============================================================================

ENV_PATH="$(dirname "$0")/../.env"
if [ -f "$ENV_PATH" ]; then
    set -a
    source "$ENV_PATH"
    set +a
    log "Loaded environment variables from .env"
else
    error ".env file not found. Please create one based on .env.example"
    exit 1
fi

# Set defaults if not provided
POSTGRES_HOST="${POSTGRES_HOST:-localhost}"
POSTGRES_PORT="${POSTGRES_PORT:-5432}"
POSTGRES_DB="${POSTGRES_DB:-nature_quest}"
POSTGRES_USER="${POSTGRES_USER:-nature_quest_user}"

# Check required variables
for var in POSTGRES_DB POSTGRES_USER POSTGRES_PASSWORD; do
    if [ -z "${!var:-}" ]; then
        error "Missing required environment variable: $var"
        exit 1
    fi
done

log "Database setup configuration:"
log "  Host: $POSTGRES_HOST"
log "  Port: $POSTGRES_PORT"
log "  Database: $POSTGRES_DB"
log "  User: $POSTGRES_USER"

# =============================================================================
# POSTGRESQL CONNECTION TEST
# =============================================================================

log "Testing PostgreSQL connection..."
if ! sudo -u postgres psql -c '\q' 2>/dev/null; then
    if ! pg_isready -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -U postgres >/dev/null 2>&1; then
        error "Cannot connect to PostgreSQL server at $POSTGRES_HOST:$POSTGRES_PORT"
        error "Please ensure PostgreSQL is running and accessible"
        error "You may need to set up PostgreSQL authentication or provide POSTGRES_ADMIN_PASSWORD"
        exit 1
    fi
fi
success "PostgreSQL server is accessible"

# =============================================================================
# DATABASE SETUP PROCESS
# =============================================================================

log "Dropping database '$POSTGRES_DB' if it exists..."
if run_psql_super "DROP DATABASE IF EXISTS \"$POSTGRES_DB\";" 2>/dev/null; then
    success "Database dropped (if existed)"
else
    warn "Could not drop database (may not exist or permission issue)"
fi

log "Checking if user '$POSTGRES_USER' exists..."
if run_psql_super "SELECT 1 FROM pg_roles WHERE rolname='$POSTGRES_USER';" 2>/dev/null | grep -q "1"; then
    log "User '$POSTGRES_USER' already exists. Updating password..."
    run_psql_super "ALTER USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';"
    success "User password updated"
else
    log "Creating user '$POSTGRES_USER'..."
    run_psql_super "CREATE USER \"$POSTGRES_USER\" WITH PASSWORD '$POSTGRES_PASSWORD';"
    success "User created"
fi

log "Creating database '$POSTGRES_DB' owned by '$POSTGRES_USER'..."
run_psql_super "CREATE DATABASE \"$POSTGRES_DB\" OWNER \"$POSTGRES_USER\";"
success "Database created"

log "Granting privileges..."
run_psql_super "GRANT ALL PRIVILEGES ON DATABASE \"$POSTGRES_DB\" TO \"$POSTGRES_USER\";"
run_psql_super "ALTER USER \"$POSTGRES_USER\" CREATEDB;"
success "Privileges granted"

# =============================================================================
# EXTENSIONS SETUP
# =============================================================================

log "Enabling required extensions in '$POSTGRES_DB'..."

extensions=("postgis" "uuid-ossp" "pg_trgm")
for ext in "${extensions[@]}"; do
        log "Installing extension: $ext"
    if ! run_psql_super "CREATE EXTENSION IF NOT EXISTS \"$ext\" WITH SCHEMA public;" "$POSTGRES_DB" 2>/dev/null; then
        warn "Could not install extension '$ext'. This might be okay for basic functionality."
    fi
done

log "Granting schema permissions..."
PGPASSWORD="${POSTGRES_ADMIN_PASSWORD:-}" psql -U postgres -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c "GRANT USAGE ON SCHEMA public TO \"$POSTGRES_USER\";"
PGPASSWORD="${POSTGRES_ADMIN_PASSWORD:-}" psql -U postgres -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c "GRANT CREATE ON SCHEMA public TO \"$POSTGRES_USER\";"

# =============================================================================
# VERIFICATION
# =============================================================================

log "Testing database connection as application user..."
if PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c '\q' 2>/dev/null; then
    success "Database connection test successful!"
else
    error "Database connection test failed!"
    exit 1
fi

log "Verifying extensions..."
PGPASSWORD="$POSTGRES_PASSWORD" psql -U "$POSTGRES_USER" -h "$POSTGRES_HOST" -p "$POSTGRES_PORT" -d "$POSTGRES_DB" -c '\dx'

echo ""
echo "To manually confirm installed extensions, run:"
echo "  psql -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB -c '\\dx'"
echo "The output should list: postgis, uuid-ossp, pg_trgm"
echo ""


# =============================================================================
# COMPLETION
# =============================================================================

success "PostgreSQL database and extensions setup completed successfully!"

echo ""
echo "Next steps:"
echo "1. Verify database connection:"
echo "   psql -U $POSTGRES_USER -h $POSTGRES_HOST -p $POSTGRES_PORT -d $POSTGRES_DB"
echo ""
echo "2. Run Django migrations:"
echo "   python manage.py makemigrations"
echo "   python manage.py migrate"
echo ""
echo "3. Create a Django superuser:"
echo "   python manage.py createsuperuser"
echo ""
echo "4. Start the development server:"
echo "   python manage.py runserver"
echo ""
echo "Database Details:"
echo "  Host: $POSTGRES_HOST"
echo "  Port: $POSTGRES_PORT"
echo "  Database: $POSTGRES_DB"
echo "  User: $POSTGRES_USER"
echo ""
