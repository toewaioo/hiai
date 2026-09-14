#!/usr/bin/env bash
set -euo pipefail

HIAI_DIR="$HOME/.local/share/hiai"
VENV_DIR="$HIAI_DIR/venv"
BIN_DIR="$HOME/.local/bin"
REPO_URL="https://github.com/hiai-ai/hiai.git"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

info()  { echo -e "${GREEN}✓${NC} $1"; }
warn()  { echo -e "${YELLOW}⚠${NC} $1"; }
fail()  { echo -e "${RED}✗${NC} $1" >&2; exit 1; }

check_python() {
    for cmd in python3.12 python3.11 python3.10 python3; do
        if command -v "$cmd" &>/dev/null; then
            PYTHON="$cmd"
            VERSION=$("$PYTHON" -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
            MAJOR=$("$PYTHON" -c "import sys; print(sys.version_info.major)")
            MINOR=$("$PYTHON" -c "import sys; print(sys.version_info.minor)")
            if [ "$MAJOR" -ge 3 ] && [ "$MINOR" -ge 10 ]; then
                info "Found Python $VERSION at $(command -v "$PYTHON")"
                return 0
            fi
        fi
    done
    fail "Python 3.10+ is required but not found. Please install Python 3.10 or later."
}

create_venv() {
    info "Creating virtual environment..."
    "$PYTHON" -m venv "$VENV_DIR"
    info "Virtual environment created at $VENV_DIR"
}

install_package() {
    info "Installing HIAI..."
    "$VENV_DIR/bin/pip" install --upgrade pip -q
    "$VENV_DIR/bin/pip" install -e "$HIAI_DIR/repo" -q
    info "HIAI installed successfully"
}

install_executable() {
    mkdir -p "$BIN_DIR"

    cat > "$BIN_DIR/hiai" <<WRAPPER
#!/usr/bin/env bash
set -euo pipefail
HIAI_HOME="${HIAI_DIR}/repo"
SRC_DIR="\${HIAI_HOME}/src"
export PYTHONPATH="\${SRC_DIR}\${PYTHONPATH:+:\$PYTHONPATH}"
exec python3 -m hiai "\$@"
WRAPPER
    chmod +x "$BIN_DIR/hiai"
    info "Created executable at $BIN_DIR/hiai"
}

check_path() {
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        warn "$BIN_DIR is not in your PATH."
        echo "  Add it to your shell profile:"
        echo ""
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo ""
        echo "  Or add it to your .bashrc / .zshrc:"
        echo '    echo \'export PATH="$HOME/.local/bin:$PATH"\' >> ~/.bashrc'
    else
        info "$BIN_DIR is already in your PATH."
    fi
}

main() {
    echo ""
    echo "  ╦ ╦╦╔═╗╦"
    echo "  ╠═╣║╠═╝║"
    echo "  ╩ ╩╩╩  ╩"
    echo ""
    echo "  HIAI Installer"
    echo "  ──────────────"
    echo ""

    check_python

    if [ -d "$HIAI_DIR/repo" ]; then
        info "Updating existing installation..."
        cd "$HIAI_DIR/repo"
        git pull -q
    else
        info "Cloning HIAI repository..."
        git clone --depth 1 "$REPO_URL" "$HIAI_DIR/repo"
    fi

    create_venv
    install_package
    install_executable
    check_path

    echo ""
    info "Installation complete!"
    echo ""
    echo "  Run 'hiai --help' to get started."
    echo "  Run 'hiai config set-key' to set your OpenRouter API key."
    echo ""
}

main "$@"
