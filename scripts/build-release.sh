#!/bin/bash
# Build release binaries for distribution
# Creates portable tarballs for Linux, macOS, and Windows

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
HIGH_AGENT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
DIST_DIR="$HIGH_AGENT_ROOT/dist"
BUILD_DIR="$DIST_DIR/build"

echo "╔══════════════════════════════════════════════════╗"
echo "║  Graph_x_0x0 Release Builder                  ║"
echo "╚══════════════════════════════════════════════════╝"

mkdir -p "$DIST_DIR" "$BUILD_DIR"
cd "$HIGH_AGENT_ROOT"

# ── Linux x86_64 musl ──────────────────────────────────────────
build_linux_musl() {
    echo ""
    echo "[*] Building: Linux x86_64 (musl)"
    rustup target add x86_64-unknown-linux-musl 2>/dev/null || true
    cargo build --features tui --release --target x86_64-unknown-linux-musl
    mkdir -p "$BUILD_DIR/high-agent-x86_64-unknown-linux-musl"
    cp rust/target/x86_64-unknown-linux-musl/release/high-agent-tui \
       "$BUILD_DIR/high-agent-x86_64-unknown-linux-musl/" 2>/dev/null || \
    cp rust/target/x86_64-unknown-linux-musl/release/high-agent \
       "$BUILD_DIR/high-agent-x86_64-unknown-linux-musl/"
    cp "$HIGH_AGENT_ROOT/rust/README.md" "$BUILD_DIR/high-agent-x86_64-unknown-linux-musl/README.txt"
    tar -C "$BUILD_DIR" -czf "$DIST_DIR/high-agent-x86_64-unknown-linux-musl.tar.gz" \
        high-agent-x86_64-unknown-linux-musl/
    echo "[+] Created: dist/high-agent-x86_64-unknown-linux-musl.tar.gz"
}

# ── Linux GNU ──────────────────────────────────────────────────
build_linux_gnu() {
    echo ""
    echo "[*] Building: Linux x86_64 (GNU)"
    cargo build --features tui --release
    mkdir -p "$BUILD_DIR/high-agent-x86_64-unknown-linux-gnu"
    cp rust/target/release/high-agent-tui "$BUILD_DIR/high-agent-x86_64-unknown-linux-gnu/" 2>/dev/null || \
    cp rust/target/release/high-agent "$BUILD_DIR/high-agent-x86_64-unknown-linux-gnu/"
    cp "$HIGH_AGENT_ROOT/rust/README.md" "$BUILD_DIR/high-agent-x86_64-unknown-linux-gnu/README.txt"
    tar -C "$BUILD_DIR" -czf "$DIST_DIR/high-agent-x86_64-unknown-linux-gnu.tar.gz" \
        high-agent-x86_64-unknown-linux-gnu/
    echo "[+] Created: dist/high-agent-x86_64-unknown-linux-gnu.tar.gz"
}

# ── macOS ──────────────────────────────────────────────────────
build_macos() {
    echo ""
    echo "[*] Building: macOS (universal)"
    cargo build --features tui --release 2>&1 || {
        echo "[!] macOS build failed (likely not on macOS)"
        return 1
    }
    mkdir -p "$BUILD_DIR/high-agent-aarch64-apple-darwin"
    cp rust/target/release/high-agent-tui "$BUILD_DIR/high-agent-aarch64-apple-darwin/" 2>/dev/null || \
    cp rust/target/release/high-agent "$BUILD_DIR/high-agent-aarch64-apple-darwin/"
    cp "$HIGH_AGENT_ROOT/rust/README.md" "$BUILD_DIR/high-agent-aarch64-apple-darwin/README.txt"
    tar -C "$BUILD_DIR" -czf "$DIST_DIR/high-agent-aarch64-apple-darwin.tar.gz" \
        high-agent-aarch64-apple-darwin/
    echo "[+] Created: dist/high-agent-aarch64-apple-darwin.tar.gz"
}

# ── Python wheel ───────────────────────────────────────────────
build_python() {
    echo ""
    echo "[*] Building: Python wheel"
    cd "$HIGH_AGENT_ROOT/python"
    python -m build --wheel 2>/dev/null || {
        pip install build --quiet 2>/dev/null
        python -m build --wheel
    }
    cp dist/*.whl "$DIST_DIR/" 2>/dev/null || echo "[!] Python wheel build skipped"
    cd "$HIGH_AGENT_ROOT"
}

# ── Summary ────────────────────────────────────────────────────
show_summary() {
    echo ""
    echo "╔══════════════════════════════════════════════════╗"
    echo "║  Release artifacts                               ║"
    echo "╚══════════════════════════════════════════════════╝"
    ls -lh "$DIST_DIR"/*.tar.gz "$DIST_DIR"/*.whl 2>/dev/null || ls -lh "$DIST_DIR"/
    echo ""
    echo "SHA256 checksums:"
    for f in "$DIST_DIR"/*.tar.gz "$DIST_DIR"/*.whl; do
        [ -f "$f" ] && sha256sum "$f"
    done
}

# ── Main ───────────────────────────────────────────────────────
case "${1:-all}" in
    linux-musl)  build_linux_musl;;
    linux-gnu)   build_linux_gnu;;
    macos)       build_macos;;
    python)      build_python;;
    all)
        build_linux_gnu
        build_python
        ;;
    clean)
        rm -rf "$DIST_DIR"/*
        echo "[+] Cleaned dist/"
        ;;
    *) echo "Usage: $0 [linux-musl|linux-gnu|macos|python|all|clean]";;
esac

show_summary
