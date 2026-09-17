#!/usr/bin/env bash
set -euo pipefail

HIAI_DIR="$HOME/.local/share/hiai"
VENV_DIR="$HIAI_DIR/venv"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/toewaioo/hiai.git"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1" >&2; exit 1; }
step()  { echo -e "${CYAN}→${NC} $1"; }

check_python() {
    for cmd in python3.12 python3.11 python3.10 python3; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON="$cmd"
            MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
            MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
                info "Found Python ${MAJOR}.${MINOR} at $(command -v "$PYTHON")"
                return 0
            fi
        fi
    done
    fail "Python 3.10+ is required but not found."
}

setup_dirs() {
    mkdir -p "$HIAI_DIR" "$BIN_DIR"
}

# Determine source: local repo or remote clone
resolve_source() {
    # Check if running from inside the repo
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$SCRIPT_DIR/pyproject.toml" ] && [ -d "$SCRIPT_DIR/src/hiai" ]; then
        info "Detected local installation from $SCRIPT_DIR"
        REPO_DIR="$SCRIPT_DIR"
        return 0
    fi

    # Check if repo already cloned
    if [ -d "$HIAI_DIR/repo" ] && [ -f "$HIAI_DIR/repo/pyproject.toml" ]; then
        info "Using existing clone at $HIAI_DIR/repo"
        REPO_DIR="$HIAI_DIR/repo"
        return 0
    fi

    # Clone from GitHub
    step "Cloning HIAI repository..."
    git clone --depth 1 "$REPO_URL" "$HIAI_DIR/repo" 2>/dev/null || fail "Failed to clone. Check your internet connection."
    REPO_DIR="$HIAI_DIR/repo"
    info "Repository cloned to $HIAI_DIR/repo"
}

create_venv() {
    if [ -d "$VENV_DIR" ]; then
        info "Virtual environment exists, reusing..."
        # Ensure pip is available
        if [ ! -f "$VENV_DIR/bin/pip" ]; then
            step "Repairing venv (missing pip)..."
            "$VENV_DIR/bin/python3" -m ensurepip --upgrade 2>/dev/null || {
                warn "Failed to repair venv, recreating..."
                rm -rf "$VENV_DIR"
                "$PYTHON" -m venv "$VENV_DIR"
            }
        fi
    else
        step "Creating virtual environment..."
        "$PYTHON" -m venv "$VENV_DIR"
        info "Virtual environment created"
    fi
}

install_package() {
    step "Installing HIAI package..."
    "$VENV_DIR/bin/python3" -m pip install --upgrade pip -q
    "$VENV_DIR/bin/python3" -m pip install -e "$REPO_DIR" -q
    info "Package installed"
}

create_executable() {
    step "Creating hiai executable..."

    cat > "$BIN_DIR/hiai" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
SRC_DIR="${REPO_DIR}/src"
export PYTHONPATH="\${SRC_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m hiai "\$@"
WRAPPER
    chmod +x "$BIN_DIR/hiai"
    info "Executable created at $BIN_DIR/hiai"
}

verify_install() {
    step "Verifying installation..."

    if ! "$BIN_DIR/hiai" --version &>/dev/null; then
        fail "Installation verification failed. Try running: $BIN_DIR/hiai --help"
    fi

    VERSION=$("$BIN_DIR/hiai" --version 2>&1)
    info "Verified: $VERSION"
}

check_path() {
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        warn "$BIN_DIR is not in your PATH."
        echo ""
        echo "  Add it by running:"
        echo ""
        echo -e "    ${CYAN}echo 'export PATH=\"\$HOME/.local/bin:\$PATH\"' >> ~/.bashrc${NC}"
        echo -e "    ${CYAN}source ~/.bashrc${NC}"
        echo ""
    else
        info "$BIN_DIR is already in your PATH."
    fi
}

main() {
    echo ""
    echo -e "${CYAN}  ╦ ╦╦╔═╗╦${NC}"
    echo -e "${CYAN}  ╠═╣║╠═╝║${NC}"
    echo -e "${CYAN}  ╩ ╩╩╩  ╩${NC}"
    echo ""
    echo "  HIAI Installer"
    echo "  ──────────────"
    echo ""

    check_python
    setup_dirs
    resolve_source
    create_venv
    install_package
    create_executable
    verify_install
    check_path

    echo ""
    info "Installation complete!"
    echo ""
    echo "  Get started:"
    echo "    hiai --help"
    echo "    hiai config set-key"
    echo ""
}

main "$@"
