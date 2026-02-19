#!/usr/bin/env bash
# Release script for zlib-rs-python (Linux / macOS)
#
# Usage:
#   ./scripts/release.sh <version>
#
# Example:
#   ./scripts/release.sh 0.2.0

set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

header() {
    echo ""
    echo -e "${CYAN}=== $1 ===${NC}"
    echo ""
}

VERSION="${1:-}"

if [[ -z "$VERSION" ]]; then
    echo -e "${RED}Usage: ./scripts/release.sh <version>${NC}"
    echo "Example: ./scripts/release.sh 0.2.0"
    exit 1
fi

if ! [[ "$VERSION" =~ ^[0-9]+\.[0-9]+\.[0-9]+(-[a-zA-Z]+(\.[0-9]+)?)?$ ]]; then
    echo -e "${RED}Error: Invalid version format '$VERSION'.${NC}"
    echo "Expected format: X.Y.Z or X.Y.Z-alpha.1"
    exit 1
fi

header "Preparing release v$VERSION"

# 1. Update Cargo.toml version
header "1/5 Updating Cargo.toml"
sed -i.bak "s/^version = \".*\"/version = \"$VERSION\"/" Cargo.toml && rm -f Cargo.toml.bak
echo -e "${GREEN}Cargo.toml updated to $VERSION${NC}"

# 2. Update __init__.py version
header "2/5 Updating __init__.py"
sed -i.bak "s/__version__ = \".*\"/__version__ = \"$VERSION\"/" python/zlib_rs/__init__.py && rm -f python/zlib_rs/__init__.py.bak
echo -e "${GREEN}__init__.py updated to $VERSION${NC}"

# 3. Build release
header "3/5 Building release"
RUSTFLAGS="-C target-cpu=native" maturin develop --release

# 4. Run tests
header "4/5 Running tests"
pytest tests/ -v

# 5. Confirm and release
header "5/5 Ready to release"
echo -e "${YELLOW}Version:  v$VERSION${NC}"
echo ""
echo "This will:"
echo "  - Commit version bump"
echo "  - Create git tag v$VERSION"
echo "  - Push tag to origin (triggers CI release pipeline)"
echo ""
read -rp "Proceed? (y/n) " confirm
if [[ "$confirm" != "y" ]]; then
    echo -e "${YELLOW}Aborted.${NC}"
    exit 0
fi

# Commit, tag, and push
BRANCH=$(git rev-parse --abbrev-ref HEAD)
git add Cargo.toml python/zlib_rs/__init__.py
git commit -m "release: v$VERSION"
git tag -a "v$VERSION" -m "Release v$VERSION"
git push origin "$BRANCH"
git push origin "v$VERSION"

echo ""
echo -e "${GREEN}=== Release v$VERSION pushed ===${NC}"
echo ""
echo "GitHub Actions will now:"
echo "  1. Build wheels for Linux, Windows, macOS"
echo "  2. Test wheels on all platforms"
echo "  3. Publish to PyPI"
echo "  4. Create GitHub Release"
echo ""
echo -e "${CYAN}Monitor progress: https://github.com/farhaanaliii/zlib-rs-python/actions${NC}"
