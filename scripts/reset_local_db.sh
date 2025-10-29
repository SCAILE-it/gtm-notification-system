#!/bin/bash
# ABOUTME: Resets local Docker Compose database and runs migrations from scratch
# ABOUTME: Use this when testing migration changes or starting fresh

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   SCAILE Notification System - Database Reset            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if we're in the right directory
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    echo -e "${YELLOW}Please run this script from the gtm-notification-system root directory${NC}"
    exit 1
fi

# Stop all containers
echo -e "${YELLOW}[1/5]${NC} Stopping Docker containers..."
docker compose down 2>/dev/null || docker-compose down 2>/dev/null || true
echo -e "${GREEN}✓ Containers stopped${NC}"
echo ""

# Remove volumes (this deletes all data)
echo -e "${YELLOW}[2/5]${NC} Removing database volumes..."
docker volume rm gtm-notification-system_postgres_data 2>/dev/null || true
docker volume rm gtm-notification-system_storage_data 2>/dev/null || true
echo -e "${GREEN}✓ Volumes removed${NC}"
echo ""

# Start containers
echo -e "${YELLOW}[3/5]${NC} Starting Docker containers..."
if command -v docker compose &> /dev/null; then
    docker compose up -d
else
    docker-compose up -d
fi
echo -e "${GREEN}✓ Containers started${NC}"
echo ""

# Wait for postgres to be ready
echo -e "${YELLOW}[4/5]${NC} Waiting for PostgreSQL to be ready..."
MAX_ATTEMPTS=30
ATTEMPT=0

while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
    if docker exec gtm-notifications-postgres pg_isready -U postgres &>/dev/null; then
        echo -e "${GREEN}✓ PostgreSQL is ready${NC}"
        break
    fi
    ATTEMPT=$((ATTEMPT + 1))
    echo -n "."
    sleep 1
done

if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
    echo -e "${RED}❌ PostgreSQL failed to start after ${MAX_ATTEMPTS} seconds${NC}"
    echo -e "${YELLOW}Check logs with: docker compose logs postgres${NC}"
    exit 1
fi
echo ""

# Verify migrations ran
echo -e "${YELLOW}[5/5]${NC} Verifying database setup..."

# Check if tables exist
TABLES_EXIST=$(docker exec gtm-notifications-postgres psql -U postgres -d postgres -t -c "
    SELECT COUNT(*)
    FROM information_schema.tables
    WHERE table_name IN ('notification_preferences', 'notification_logs')
" | tr -d ' ')

if [ "$TABLES_EXIST" = "2" ]; then
    echo -e "${GREEN}✓ Database migrations completed successfully${NC}"

    # Show test users
    echo ""
    echo -e "${BLUE}📋 Test users available:${NC}"
    docker exec gtm-notifications-postgres psql -U postgres -d postgres -c "
        SELECT id, email, email_confirmed_at
        FROM auth.users
        ORDER BY email
    " 2>/dev/null || echo -e "${YELLOW}⚠️  Could not fetch test users${NC}"
else
    echo -e "${RED}❌ Database migrations failed${NC}"
    echo -e "${YELLOW}Tables created: ${TABLES_EXIST}/2${NC}"
    exit 1
fi

echo ""
echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║   ✅ Database Reset Complete!                            ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${GREEN}Services running:${NC}"
echo -e "  • PostgreSQL:    ${BLUE}localhost:5432${NC}"
echo -e "  • MailHog Web:   ${BLUE}http://localhost:8025${NC}"
echo -e "  • MailHog SMTP:  ${BLUE}localhost:1025${NC}"
echo -e "  • Auth:          ${BLUE}http://localhost:9999${NC}"
echo -e "  • PostgREST:     ${BLUE}http://localhost:3000${NC}"
echo -e "  • Storage:       ${BLUE}http://localhost:5000${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo -e "  1. Run tests:        ${BLUE}python tests/test_full_flow.py${NC}"
echo -e "  2. View emails:      ${BLUE}open http://localhost:8025${NC}"
echo -e "  3. Check logs:       ${BLUE}docker compose logs -f${NC}"
echo ""
