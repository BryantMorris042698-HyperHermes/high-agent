#!/bin/bash
# Install script for Graph_x_0x0
# Supports: Linux, macOS, Termux (Android), WSL

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIGH_AGENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

echo "============================================"
echo "  Graph_x_0x0 Installer"
echo "  Φ(G) = α·Q(G) − β·Č(G) − γ·mean(V)"
echo "============================================"

detect_os() {
    case "$(uname -s)" in
        Linux*)     echo "linux";;
        Darwin*)    echo "macos";;
        * Termux*)  echo "termux";;
        MINGW*|MSYS*|CYGWIN*) echo "windows";;
        *)          echo "unknown";;
    esac
}

detect_rust() {
    if command -v rustc &>/dev/null; then
        echo "rust"
    elif command -v python3 &>/dev/null; then
        echo "python"
    else
        echo "none"
    fi
}

install_rust() {
    echo "[+] Installing Rust..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --default-toolchain stable
    source "$HOME/.cargo/env"
    echo "[+] Rust installed: $(rustc --version)"
}

install_python_deps() {
    echo "[+] Installing Python dependencies..."
    pip install -e "$HIGH_AGENT_ROOT/python/" --quiet 2>/dev/null || \
    pip3 install -e "$HIGH_AGENT_ROOT/python/" --quiet 2>/dev/null
    echo "[+] Python engine ready"
}

build_rust() {
    echo "[+] Building Rust engine (core only)..."
    source "$HOME/.cargo/env" 2>/dev/null || true
    cd "$HIGH_AGENT_ROOT/rust"
    cargo build
    echo "[+] Core binary: target/debug/high-agent"
}

build_rust_tui() {
    echo "[+] Building Rust TUI..."
    source "$HOME/.cargo/env" 2>/dev/null || true
    cd "$HIGH_AGENT_ROOT/rust"
    cargo build --features tui --release
    echo "[+] TUI binary: target/release/high-agent-tui"
}

setup_directories() {
    echo "[+] Setting up directories..."
    mkdir -p "$HOME/.high-agent"
    mkdir -p "$HOME/.high-agent/skills"
    mkdir -p "$HOME/.high-agent/repos"
    mkdir -p "$HOME/.high-agent/state"
    echo "[+] Directories created at ~/.high-agent/"
}

main() {
    OS=$(detect_os)
    echo "[*] Detected OS: $OS"

    RUST_AVAIL=$(detect_rust)
    echo "[*] Rust available: $RUST_AVAIL"

    case "${1:-all}" in
        rust)
            if [ "$RUST_AVAIL" = "none" ]; then install_rust; fi
            build_rust
            setup_directories
            ;;
        rust-tui)
            if [ "$RUST_AVAIL" = "none" ]; then install_rust; fi
            build_rust_tui
            setup_directories
            ;;
        python)
            install_python_deps
            setup_directories
            ;;
        all)
            if [ "$RUST_AVAIL" = "none" ]; then install_rust; fi
            build_rust
            install_python_deps
            setup_directories
            ;;
        help|-h|--help)
            echo "Usage: $0 [rust|rust-tui|python|all]"
            echo "  rust     - Build core engine only (fast)"
            echo "  rust-tui - Build full TUI dashboard"
            echo "  python   - Install Python engine only"
            echo "  all      - Everything (default)"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [rust|rust-tui|python|all]"
            exit 1
            ;;
    esac

    echo ""
    echo "============================================"
    echo "  Installation complete!"
    echo "============================================"
    echo ""
    echo "Quick start:"
    echo "  Rust CLI:  cargo run --features tui"
    echo "  Python:    cd python && python high-agent-repl.py"
    echo "  TUI:       target/release/high-agent-tui"
    echo ""
    echo "Documentation: $HIGH_AGENT_ROOT/rust/README.md"
}

main "$@"
