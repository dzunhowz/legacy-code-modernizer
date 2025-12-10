#!/bin/bash
# Quick start script for MCP client testing

echo "======================================"
echo "Legacy Code Modernizer MCP Client"
echo "======================================"
echo ""
echo "Choose an option:"
echo "  1) Run automated test suite"
echo "  2) Start interactive client"
echo "  3) Start MCP server only"
echo ""
read -p "Enter choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "Running automated tests..."
    uv run python examples/mcp_client_test.py
    ;;
  2)
    echo ""
    echo "Starting interactive client..."
    echo "(Type 'list' to see available commands)"
    uv run python examples/mcp_client_interactive.py
    ;;
  3)
    echo ""
    echo "Starting MCP server..."
    echo "(Press Ctrl+C to stop)"
    uv run python -m src.mcp_server.server
    ;;
  *)
    echo "Invalid choice"
    exit 1
    ;;
esac
