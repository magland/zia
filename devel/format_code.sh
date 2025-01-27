#!/bin/bash

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

# Format Python code
echo "Formatting Python code..."
black "$PROJECT_ROOT/zia_benchmark/src/zia_benchmark"

# Format TypeScript/JavaScript code
echo "Formatting TypeScript/JavaScript code..."
cd "$PROJECT_ROOT/web-ui" && npm run format

echo "Code formatting complete!"
