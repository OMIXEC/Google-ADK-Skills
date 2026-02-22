#!/bin/bash
#
# ADK Agent Test Runner
#
# Usage:
#   ./run_tests.sh              # Run all tests
#   ./run_tests.sh unit         # Run unit tests only
#   ./run_tests.sh integration  # Run integration tests
#   ./run_tests.sh evaluation   # Run evaluation benchmarks
#   ./run_tests.sh quick        # Run quick tests (no slow)
#   ./run_tests.sh coverage     # Run with coverage report
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
TESTS_DIR="${TESTS_DIR:-tests}"
COVERAGE_DIR="${COVERAGE_DIR:-htmlcov}"
TIMEOUT="${TEST_TIMEOUT:-60}"

# Print header
print_header() {
    echo ""
    echo "========================================"
    echo "  ADK Agent Test Runner"
    echo "========================================"
    echo ""
}

# Print usage
print_usage() {
    echo "Usage: $0 [command]"
    echo ""
    echo "Commands:"
    echo "  unit         Run unit tests only (fast, no API calls)"
    echo "  integration  Run integration tests (requires API key)"
    echo "  evaluation   Run evaluation benchmarks (slow)"
    echo "  quick        Run all tests except slow ones"
    echo "  coverage     Run tests with coverage report"
    echo "  all          Run all tests"
    echo "  help         Show this help message"
    echo ""
    echo "Environment Variables:"
    echo "  GOOGLE_API_KEY   API key for integration tests"
    echo "  TEST_TIMEOUT     Timeout in seconds (default: 60)"
    echo "  TEST_MODEL       Model to use (default: gemini-1.5-flash)"
    echo ""
}

# Check dependencies
check_dependencies() {
    if ! command -v pytest &> /dev/null; then
        echo -e "${RED}Error: pytest not found. Install with: pip install pytest${NC}"
        exit 1
    fi
}

# Check API key for integration tests
check_api_key() {
    if [ -z "$GOOGLE_API_KEY" ]; then
        echo -e "${YELLOW}Warning: GOOGLE_API_KEY not set. Integration tests will be skipped.${NC}"
        return 1
    fi
    return 0
}

# Run unit tests
run_unit_tests() {
    echo -e "${GREEN}Running unit tests...${NC}"
    pytest "$TESTS_DIR" -v \
        -m "not integration and not evaluation and not slow" \
        --timeout="$TIMEOUT"
}

# Run integration tests
run_integration_tests() {
    echo -e "${GREEN}Running integration tests...${NC}"

    if ! check_api_key; then
        echo -e "${YELLOW}Skipping integration tests (no API key)${NC}"
        return 0
    fi

    pytest "$TESTS_DIR" -v \
        -m "integration" \
        --timeout="$TIMEOUT"
}

# Run evaluation tests
run_evaluation_tests() {
    echo -e "${GREEN}Running evaluation tests...${NC}"

    if ! check_api_key; then
        echo -e "${YELLOW}Skipping evaluation tests (no API key)${NC}"
        return 0
    fi

    pytest "$TESTS_DIR" -v \
        -m "evaluation" \
        --timeout=300
}

# Run quick tests (no slow)
run_quick_tests() {
    echo -e "${GREEN}Running quick tests...${NC}"
    pytest "$TESTS_DIR" -v \
        -m "not slow" \
        --timeout="$TIMEOUT"
}

# Run all tests
run_all_tests() {
    echo -e "${GREEN}Running all tests...${NC}"
    pytest "$TESTS_DIR" -v \
        --timeout=300
}

# Run tests with coverage
run_coverage() {
    echo -e "${GREEN}Running tests with coverage...${NC}"

    # Check for pytest-cov
    if ! python -c "import pytest_cov" &> /dev/null; then
        echo -e "${YELLOW}Installing pytest-cov...${NC}"
        pip install pytest-cov
    fi

    pytest "$TESTS_DIR" -v \
        --cov=. \
        --cov-report=html:"$COVERAGE_DIR" \
        --cov-report=term-missing \
        -m "not slow" \
        --timeout="$TIMEOUT"

    echo ""
    echo -e "${GREEN}Coverage report generated: $COVERAGE_DIR/index.html${NC}"
}

# Main
main() {
    print_header
    check_dependencies

    case "${1:-all}" in
        unit)
            run_unit_tests
            ;;
        integration)
            run_integration_tests
            ;;
        evaluation)
            run_evaluation_tests
            ;;
        quick)
            run_quick_tests
            ;;
        coverage)
            run_coverage
            ;;
        all)
            run_all_tests
            ;;
        help|--help|-h)
            print_usage
            ;;
        *)
            echo -e "${RED}Unknown command: $1${NC}"
            print_usage
            exit 1
            ;;
    esac

    echo ""
    echo -e "${GREEN}Done!${NC}"
}

main "$@"
