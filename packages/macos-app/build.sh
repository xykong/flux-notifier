#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

CONFIGURATION="${1:-release}"
BUILD_DIR=".build/$CONFIGURATION"
APP_NAME="FluxNotifier"
APP_BUNDLE="$SCRIPT_DIR/build/${APP_NAME}.app"

echo "Building FluxNotifier ($CONFIGURATION)..."

swift build -c "$CONFIGURATION" 2>&1

echo "Assembling .app bundle..."

rm -rf "$APP_BUNDLE"
mkdir -p "$APP_BUNDLE/Contents/MacOS"
mkdir -p "$APP_BUNDLE/Contents/Resources"

cp "$BUILD_DIR/$APP_NAME" "$APP_BUNDLE/Contents/MacOS/$APP_NAME"

cp "Info.plist" "$APP_BUNDLE/Contents/Info.plist"

if [ -f "Resources/AppIcon.icns" ]; then
    cp "Resources/AppIcon.icns" "$APP_BUNDLE/Contents/Resources/AppIcon.icns"
fi

echo ""
echo "✓ Built: $APP_BUNDLE"
echo ""
echo "Run with:"
echo "  open $APP_BUNDLE"
echo ""
echo "Or install to /Applications:"
echo "  cp -r $APP_BUNDLE /Applications/"
