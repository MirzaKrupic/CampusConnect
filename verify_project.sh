#!/bin/bash

# Project Structure Verification Script
# Ensures all required files are present

echo "=========================================="
echo "CampusConnect Project Verification"
echo "=========================================="
echo ""

EXIT_CODE=0

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if file exists
check_file() {
    if [ -f "$1" ]; then
        echo -e "  ${GREEN}✓${NC} $1"
    else
        echo -e "  ${RED}✗${NC} $1 (MISSING)"
        EXIT_CODE=1
    fi
}

# Check if directory exists
check_dir() {
    if [ -d "$1" ]; then
        echo -e "  ${GREEN}✓${NC} $1/"
    else
        echo -e "  ${RED}✗${NC} $1/ (MISSING)"
        EXIT_CODE=1
    fi
}

echo "Configuration Files:"
check_file "docker-compose.yml"
check_file "Dockerfile"
check_file "requirements.txt"
check_file ".env.example"
check_file ".gitignore"
check_file "Makefile"
echo ""

echo "Documentation:"
check_file "README.md"
check_file "QUICKSTART.md"
check_file "API_EXAMPLES.sh"
check_file "PROJECT_SUMMARY.md"
echo ""

echo "Backend Structure:"
check_dir "backend"
check_file "backend/main.py"
check_file "backend/config.py"
echo ""

echo "Database Clients:"
check_dir "backend/db"
check_file "backend/db/__init__.py"
check_file "backend/db/postgres.py"
check_file "backend/db/redis.py"
check_file "backend/db/mongo.py"
check_file "backend/db/neo4j.py"
echo ""

echo "Models:"
check_dir "backend/models"
check_file "backend/models/__init__.py"
check_file "backend/models/user.py"
check_file "backend/models/group.py"
check_file "backend/models/post.py"
echo ""

echo "Services:"
check_dir "backend/services"
check_file "backend/services/__init__.py"
check_file "backend/services/user_service.py"
check_file "backend/services/group_service.py"
check_file "backend/services/post_service.py"
check_file "backend/services/recommendation_service.py"
echo ""

echo "Routers:"
check_dir "backend/routers"
check_file "backend/routers/__init__.py"
check_file "backend/routers/users.py"
check_file "backend/routers/groups.py"
check_file "backend/routers/posts.py"
check_file "backend/routers/recommendations.py"
echo ""

echo "Tests:"
check_dir "backend/tests"
check_file "backend/tests/__init__.py"
check_file "backend/tests/test_services.py"
echo ""

echo "Database Initialization:"
check_dir "docker/init"
check_file "docker/init/postgres-init.sql"
check_file "docker/init/seed.py"
echo ""

# Count lines of code
echo "=========================================="
echo "Project Statistics"
echo "=========================================="
echo ""

if command -v find &> /dev/null && command -v wc &> /dev/null; then
    PY_FILES=$(find backend -name "*.py" 2>/dev/null | wc -l)
    PY_LINES=$(find backend -name "*.py" -exec wc -l {} + 2>/dev/null | tail -1 | awk '{print $1}')
    echo "Python files: $PY_FILES"
    echo "Python lines of code: $PY_LINES"
    echo ""
fi

# Check for required Python packages
echo "Required Python Packages:"
echo "  - fastapi"
echo "  - uvicorn"
echo "  - asyncpg (PostgreSQL)"
echo "  - redis"
echo "  - motor (MongoDB)"
echo "  - neo4j"
echo "  - pydantic"
echo "  - pytest"
echo ""

# Final result
echo "=========================================="
if [ $EXIT_CODE -eq 0 ]; then
    echo -e "${GREEN}✓ All required files present!${NC}"
    echo ""
    echo "Project is ready to run:"
    echo "  1. docker-compose up --build"
    echo "  2. Wait for 'Seed completed successfully!'"
    echo "  3. Access http://localhost:8000/docs"
else
    echo -e "${RED}✗ Some files are missing!${NC}"
    echo "Please ensure all files are created."
fi
echo "=========================================="
echo ""

exit $EXIT_CODE
