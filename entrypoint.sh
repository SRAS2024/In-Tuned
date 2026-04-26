#!/bin/bash
# entrypoint.sh - Runtime validation and startup script for In-Tuned.
#
# Runs at container start time (not build time) to:
#   1. Validate required environment variables.
#   2. Test database connectivity.
#   3. Validate the WSGI application can import.
#   4. Optionally run alembic migrations when RUN_MIGRATIONS=1.
#   5. exec the CMD (gunicorn, alembic, pytest, ...).

set -euo pipefail

# Colors for output (only when stdout is a tty so logs stay clean).
if [ -t 1 ]; then
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[1;33m'
    NC='\033[0m'
else
    RED=''
    GREEN=''
    YELLOW=''
    NC=''
fi

echo "=============================================="
echo "  In-Tuned Application Startup"
echo "=============================================="

# -----------------------------------------------------------------------------
# 1. Environment validation
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[1/4] Validating environment configuration...${NC}"

MISSING_VARS=()

if [ -z "${DATABASE_URL:-}" ]; then
    MISSING_VARS+=("DATABASE_URL")
fi

if [ -z "${SECRET_KEY:-}" ]; then
    echo -e "${YELLOW}WARNING: SECRET_KEY not set, using default (not recommended for production)${NC}"
fi

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    echo -e "${RED}ERROR: Missing required environment variables:${NC}"
    for var in "${MISSING_VARS[@]}"; do
        echo -e "  - $var"
    done
    echo ""
    echo "Please set these variables in your deployment configuration."
    exit 1
fi

echo -e "${GREEN}Environment configuration valid.${NC}"

# -----------------------------------------------------------------------------
# 2. Database connectivity
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[2/4] Testing database connectivity...${NC}"

python3 << 'EOF'
import os
import sys

try:
    import psycopg
    from psycopg.rows import dict_row

    database_url = os.environ.get("DATABASE_URL", "")

    # Handle Railway's postgres:// vs postgresql:// URL format
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)

    # Quick connection test with timeout
    with psycopg.connect(database_url, connect_timeout=10) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("SELECT 1 as test")
            result = cur.fetchone()
            if result and result.get('test') == 1:
                print("Database connection successful.")
                sys.exit(0)
            else:
                print("Database connection test failed: unexpected result")
                sys.exit(1)

except psycopg.OperationalError as e:
    print(f"Database connection failed: {e}")
    print("\nPlease check:")
    print("  - DATABASE_URL is correct")
    print("  - Database server is running and accessible")
    print("  - Network/firewall settings allow the connection")
    sys.exit(1)
except Exception as e:
    print(f"Database connection error: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Database connectivity check failed.${NC}"
    exit 1
fi

echo -e "${GREEN}Database connection verified.${NC}"

# -----------------------------------------------------------------------------
# 3. WSGI application validation
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[3/4] Validating application loads...${NC}"

python3 << 'EOF'
import sys
try:
    from wsgi import application
    print("WSGI application loads successfully.")
    sys.exit(0)
except Exception as e:
    print(f"Application failed to load: {e}")
    sys.exit(1)
EOF

if [ $? -ne 0 ]; then
    echo -e "${RED}Application validation failed.${NC}"
    exit 1
fi

echo -e "${GREEN}Application validated.${NC}"

# -----------------------------------------------------------------------------
# 4. Optional alembic migrations (RUN_MIGRATIONS=1 to enable)
# -----------------------------------------------------------------------------
echo -e "\n${YELLOW}[4/4] Optional database migrations...${NC}"
if [ "${RUN_MIGRATIONS:-0}" = "1" ]; then
    echo "RUN_MIGRATIONS=1 - running 'alembic upgrade head'..."
    alembic upgrade head
    echo -e "${GREEN}Migrations complete.${NC}"
else
    echo "Skipped (set RUN_MIGRATIONS=1 to apply migrations on startup)."
fi

echo -e "\n${GREEN}=============================================="
echo "  All checks passed - Starting application..."
echo "==============================================${NC}\n"

# Execute the CMD passed to the container.
exec "$@"
