#!/bin/bash

# Environment Management Script for FastAPI Backend
# Usage: ./scripts/set-env.sh [development|production|test]

set -e

# Default to development if no argument provided
ENV=${1:-development}

# Validate environment argument
if [[ ! "$ENV" =~ ^(development|production|test)$ ]]; then
    echo "Error: Invalid environment '$ENV'"
    echo "Usage: $0 [development|production|test]"
    exit 1
fi

# Get script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BACKEND_DIR="$(dirname "$SCRIPT_DIR")"

# Copy the appropriate environment file
ENV_FILE="$BACKEND_DIR/.env.$ENV"
TARGET_FILE="$BACKEND_DIR/.env"

if [[ ! -f "$ENV_FILE" ]]; then
    echo "Error: Environment file '$ENV_FILE' not found"
    exit 1
fi

# Backup existing .env if it exists
if [[ -f "$TARGET_FILE" ]]; then
    cp "$TARGET_FILE" "$TARGET_FILE.backup"
    echo "Backed up existing .env to .env.backup"
fi

# Copy environment file
cp "$ENV_FILE" "$TARGET_FILE"

echo "Successfully set environment to: $ENV"
echo "Environment file: $ENV_FILE -> $TARGET_FILE"

# Show current environment settings
echo ""
echo "Current environment settings:"
echo "----------------------------"
grep -E '^[A-Z_]+=.*' "$TARGET_FILE" | head -10

echo ""
echo "Environment setup complete!"
echo "You can now run: uvicorn doc_app_backend.main:app --reload"