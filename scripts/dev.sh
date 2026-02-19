#!/usr/bin/env bash
# zlib-rs-python development script (Linux / macOS)
# Usage: ./scripts/dev.sh <command>

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

cmd_build() {
    header "Building (release)"
    RUSTFLAGS="-C target-cpu=native" maturin develop --release
}

cmd_build_debug() {
    header "Building (debug)"
    maturin develop
}

cmd_test() {
    header "Running tests"
    pytest tests/ -v
}

cmd_bench() {
    header "Running benchmarks"
    python benchmarks/bench_zlib.py
}

cmd_clean() {
    header "Cleaning build artifacts"
    rm -rf target/ dist/ build/
    find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
    find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
    echo -e "${GREEN}Done.${NC}"
}

cmd_all() {
    cmd_build
    cmd_test
    cmd_bench
}

cmd_help() {
    echo ""
    echo -e "${YELLOW}zlib-rs-python development script${NC}"
    echo ""
    echo "Usage: ./scripts/dev.sh <command>"
    echo ""
    echo "Commands:"
    echo "  build        Build release version with native CPU optimizations"
    echo "  build-debug  Build debug version (faster compile)"
    echo "  test         Run tests with pytest"
    echo "  bench        Run performance benchmarks"
    echo "  clean        Remove build artifacts"
    echo "  all          Build (release) + test + benchmark"
    echo "  help         Show this help message"
    echo ""
}

case "${1:-help}" in
    build)       cmd_build ;;
    build-debug) cmd_build_debug ;;
    test)        cmd_test ;;
    bench)       cmd_bench ;;
    clean)       cmd_clean ;;
    all)         cmd_all ;;
    help)        cmd_help ;;
    *)
        echo "Unknown command: $1"
        cmd_help
        exit 1
        ;;
esac
