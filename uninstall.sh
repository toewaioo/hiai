#!/usr/bin/env bash
set -euo pipefail

HIAI_DIR="$HOME/.local/share/hiai"
BIN_DIR="$HOME/.local/bin"
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/hiai"

RED='\033[0;31m'
GREEN='\033[0;32m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "⚠ $1"; }

echo ""
echo "  HIAI Uninstaller"
echo "  ────────────────"
echo ""

# Remove wrapper
if [ -f "$BIN_DIR/hiai" ]; then
    rm -f "$BIN_DIR/hiai"
    info "Removed $BIN_DIR/hiai"
fi

# Remove installation directory
if [ -d "$HIAI_DIR" ]; then
    rm -rf "$HIAI_DIR"
    info "Removed $HIAI_DIR"
fi

# Ask about config
if [ -d "$CONFIG_DIR" ]; then
    echo ""
    warn "Configuration directory found at: $CONFIG_DIR"
    read -p "  Remove configuration? [y/N]: " answer
    if [[ "$answer" =~ ^[Yy]$ ]]; then
        rm -rf "$CONFIG_DIR"
        info "Removed configuration directory"
    else
        info "Keeping configuration at $CONFIG_DIR"
    fi
fi

echo ""
info "HIAI has been uninstalled."
echo ""
