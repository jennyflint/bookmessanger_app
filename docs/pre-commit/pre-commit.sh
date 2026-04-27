#!/bin/bash

# ==========================================
# 1. DOCKER CHECK
# ==========================================
# Check if the container is running; required for linting and testing
if ! docker ps | grep -q "api_app"; then
    echo "❌ Error: Container api_app is not running."
    echo "Please run 'docker compose up -d' first"
    exit 1
fi

# ==========================================
# 2. AUTOGENERATE REQUIREMENTS.TXT
# ==========================================
# Check if requirements.in is among the staged files
if git diff --cached --name-only | grep -q "^requirements.in$"; then
    echo "📦 requirements.in changed. Recompiling requirements.txt..."
    
    # Install pip-tools and compile requirements inside the container
    docker exec api_app bash -c "pip install pip-tools && pip-compile requirements.in"
    if [ $? -ne 0 ]; then
        echo "❌ Error: Failed to compile requirements.in!"
        exit 1
    fi
    
    # Automatically stage the updated requirements.txt for this commit
    git add requirements.txt
    echo "✅ requirements.txt successfully updated and staged."
fi

# ==========================================
# 3. CYRILLIC CHECK (LOCAL)
# ==========================================
echo "🔍 Checking for Cyrillic characters in staged Python files..."
# Get a list of staged .py files to prevent non-English characters in the codebase
STAGED_PY_FILES=$(git diff --cached --name-only --diff-filter=ACM | grep '\.py$' || true)

if [ -n "$STAGED_PY_FILES" ]; then
    # Search for Cyrillic letters across the staged files
    if grep -HnE "[А-Яа-яЁёІіЇїЄєҐґ]" $STAGED_PY_FILES; then
        echo "❌ Error: Cyrillic characters found in the files above!"
        echo "Please use only English for code, variables, and comments."
        exit 1
    fi
fi

# ==========================================
# 4. RUN LINTERS DIRECTLY (NO PRE-COMMIT)
# ==========================================
echo "🐳 Running Ruff and Mypy inside Docker..."

# Run Ruff for linting and formatting checks
# The dot (.) at the end means "check the entire project in the /api_app folder"
docker exec api_app ruff check .
RUFF_RESULT=$?

docker exec api_app ruff format --check .
FORMAT_RESULT=$?

# Run Mypy for static type checking
docker exec api_app mypy .
MYPY_RESULT=$?

# Stop the commit if any linting or typing issues are found
if [ $RUFF_RESULT -ne 0 ] || [ $FORMAT_RESULT -ne 0 ] || [ $MYPY_RESULT -ne 0 ]; then
    echo "❌ Code check failed. Please fix the issues above."
    exit 1
fi

# ==========================================
# 5. RUN TESTS
# ==========================================
echo "🧪 Running tests inside Docker..."
# Ensure all tests pass before allowing the commit
docker exec api_app pytest
if [ $? -ne 0 ]; then
    echo "❌ Tests failed. Commit aborted!"
    exit 1
fi

echo "✅ All checks passed! Commit created."
exit 0