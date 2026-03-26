#!/bin/bash
#
# Pre-push CI script - Run all checks locally before pushing
# Usage: ./scripts/pre_push.sh
#
# This runs the same checks as the GitHub Actions CI pipeline.
# Run this before pushing to catch issues early.
#

set -e  # Exit on first error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "🚀 Running Pre-Push CI Checks"
echo "========================================"

# Activate virtual environment if not already active
if [[ -z "$VIRTUAL_ENV" ]]; then
    if [[ -d "venv" ]]; then
        source venv/bin/activate
    elif [[ -d ".venv" ]]; then
        source .venv/bin/activate
    else
        echo -e "${RED}❌ No virtual environment found. Create one with: python -m venv venv${NC}"
        exit 1
    fi
fi

echo ""
echo -e "${YELLOW}Step 1/5: Ruff Linter${NC}"
echo "----------------------------------------"
ruff check src/ tests/
echo -e "${GREEN}✅ Linting passed${NC}"

echo ""
echo -e "${YELLOW}Step 2/5: Ruff Formatter${NC}"
echo "----------------------------------------"
ruff format --check src/ tests/
echo -e "${GREEN}✅ Formatting check passed${NC}"

echo ""
echo -e "${YELLOW}Step 3/5: Unit Tests${NC}"
echo "----------------------------------------"
pytest tests/unit/ -v --tb=short -q
echo -e "${GREEN}✅ Unit tests passed${NC}"

echo ""
echo -e "${YELLOW}Step 4/5: Architecture Tests${NC}"
echo "----------------------------------------"
pytest tests/arch/ -v --tb=short -q
echo -e "${GREEN}✅ Architecture tests passed${NC}"

echo ""
echo -e "${YELLOW}Step 5/5: Integration Tests (if DB available)${NC}"
echo "----------------------------------------"
if [[ -n "$DATABASE_URL" ]]; then
    pytest tests/integration/ -v --tb=short -q
    echo -e "${GREEN}✅ Integration tests passed${NC}"
else
    echo -e "${YELLOW}⚠️  Skipped - DATABASE_URL not set${NC}"
fi

echo ""
echo "========================================"
echo -e "${GREEN}✅ All pre-push checks passed!${NC}"
echo "========================================"
echo ""
echo "Safe to push. Run: git push origin main"
