#!/bin/bash

# KUYAN Version Bumping Script
# Usage: ./bump-version.sh [major|minor|patch]

TYPE=${1:-patch}
CURRENT=$(cat VERSION 2>/dev/null || echo "0.0.0")

IFS='.' read -ra PARTS <<< "$CURRENT"
MAJOR=${PARTS[0]:-0}
MINOR=${PARTS[1]:-0}
PATCH=${PARTS[2]:-0}

case $TYPE in
  major)
    MAJOR=$((MAJOR + 1))
    MINOR=0
    PATCH=0
    ;;
  minor)
    MINOR=$((MINOR + 1))
    PATCH=0
    ;;
  patch)
    PATCH=$((PATCH + 1))
    ;;
  *)
    echo "Usage: $0 [major|minor|patch]"
    echo ""
    echo "  major - Breaking changes (1.0.0 → 2.0.0)"
    echo "  minor - New features (1.0.0 → 1.1.0)"
    echo "  patch - Bug fixes (1.0.0 → 1.0.1)"
    exit 1
    ;;
esac

NEW_VERSION="${MAJOR}.${MINOR}.${PATCH}"

echo "================================"
echo "      KUYAN Version Bump"
echo "================================"
echo ""
echo "Current version: $CURRENT"
echo "New version:     $NEW_VERSION"
echo "Bump type:       $TYPE"
echo ""
read -p "Proceed with version bump? (y/n) " -n 1 -r
echo
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
  # Update VERSION file
  echo "$NEW_VERSION" > VERSION

  # Git operations
  git add VERSION
  git commit -m "chore: Bump version to $NEW_VERSION"
  git tag -a "v${NEW_VERSION}" -m "Release version ${NEW_VERSION}"

  echo "✅ Version bumped successfully!"
  echo ""
  echo "Next steps:"
  echo "  1. git push origin main"
  echo "  2. git push origin v${NEW_VERSION}"
  echo "  3. ./scripts/docker-build.sh"
  echo ""
else
  echo "❌ Version bump cancelled"
  exit 1
fi
