#!/usr/bin/env bash
# run.sh — one-click runner for the 4×25m Tubehouse floorplan generator
# -----------------------------------------------------------------------
# What this script does:
#   1. Checks that FreeCAD is available (PATH or common install locations).
#   2. Checks that `uv` is available.
#   3. If either is missing, prints setup instructions and exits.
#   4. If both are present:
#        a. Starts `uvx freecad-mcp` in the background.
#        b. Launches FreeCAD headless (freecadcmd) to run generate_floorplan.py.
#        c. Prints a success summary with output file locations.
#
# Usage:
#   chmod +x run.sh
#   ./run.sh
#
# Override FreeCAD executable:
#   FREECAD_CMD=/custom/path/to/FreeCADCmd ./run.sh

set -euo pipefail

# ── Colour helpers ────────────────────────────────────────────────────────────
BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'  # no colour

ok()   { echo -e "  ${GREEN}✓${NC}  $*"; }
warn() { echo -e "  ${YELLOW}!${NC}  $*"; }
err()  { echo -e "  ${RED}✗${NC}  $*"; }
sep()  { echo "──────────────────────────────────────────────────────────────"; }

echo ""
echo -e "${BOLD}  4×25m Tubehouse — FreeCAD Floorplan Generator${NC}"
sep

# ── Locate script directory (works regardless of cwd) ────────────────────────
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SPEC_FILE="$SCRIPT_DIR/spec/floorplan-spec.json"
GENERATOR="$SCRIPT_DIR/src/generate_floorplan.py"
OUT_DIR="$SCRIPT_DIR/output"
MCP_PID=""

cleanup() {
    if [[ -n "$MCP_PID" ]]; then
        kill "$MCP_PID" &>/dev/null || true
        ok "freecad-mcp stopped."
    fi
}

trap cleanup EXIT

# ── 1. Find FreeCAD ───────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 1 — Checking for FreeCAD${NC}"

FREECAD_CMD="${FREECAD_CMD:-}"

if [[ -z "$FREECAD_CMD" ]]; then
    # Probe common install locations (macOS, Linux, Windows/WSL)
    CANDIDATES=(
        "freecadcmd"
        "FreeCADCmd"
        "FreeCAD"
        "/Applications/FreeCAD.app/Contents/MacOS/FreeCADCmd"
        "/usr/lib/freecad/bin/FreeCADCmd"
        "/usr/bin/freecadcmd"
        "/snap/bin/freecad"
        "/opt/freecad/bin/FreeCADCmd"
        "C:/Program Files/FreeCAD 0.21/bin/FreeCADCmd.exe"
        "C:/Program Files/FreeCAD 1.0/bin/FreeCADCmd.exe"
    )

    for candidate in "${CANDIDATES[@]}"; do
        if command -v "$candidate" &>/dev/null 2>&1; then
            FREECAD_CMD="$candidate"
            break
        fi
        # Also try as a literal path
        if [[ -f "$candidate" ]]; then
            FREECAD_CMD="$candidate"
            break
        fi
    done
fi

FREECAD_MISSING=false
if [[ -z "$FREECAD_CMD" ]]; then
    FREECAD_MISSING=true
    err "FreeCAD not found on PATH or common install locations."
else
    ok "FreeCAD found: $FREECAD_CMD"
fi

# ── 2. Find uv ────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 2 — Checking for uv${NC}"

UV_MISSING=false
if ! command -v uv &>/dev/null 2>&1; then
    UV_MISSING=true
    err "uv not found on PATH."
else
    UV_VERSION="$(uv --version 2>/dev/null || echo 'unknown')"
    ok "uv found: $UV_VERSION"
fi

# ── 3. Setup instructions if anything is missing ─────────────────────────────
if $FREECAD_MISSING || $UV_MISSING; then
    echo ""
    sep
    warn "One or more prerequisites are missing.  Setup instructions:"
    echo ""

    if $FREECAD_MISSING; then
        echo "  FreeCAD:"
        echo "    Download:  https://www.freecad.org/downloads.php"
        echo "    macOS:     brew install --cask freecad"
        echo "    Ubuntu:    sudo apt install freecad"
        echo "    Windows:   Download installer from the link above and add"
        echo "               'C:\\Program Files\\FreeCAD 0.21\\bin' to your PATH."
        echo "    Verify:    freecadcmd --version"
        echo ""
        echo "    Or set the FREECAD_CMD env variable to the full path:"
        echo "      FREECAD_CMD=/path/to/FreeCADCmd ./run.sh"
        echo ""
    fi

    if $UV_MISSING; then
        echo "  uv (fast Python package runner):"
        echo "    macOS/Linux:  curl -LsSf https://astral.sh/uv/install.sh | sh"
        echo "    Windows:      irm https://astral.sh/uv/install.ps1 | iex"
        echo "    Verify:       uv --version"
        echo ""
    fi

    sep
    echo ""
    exit 1
fi

# ── 4. Ensure output directories exist ───────────────────────────────────────
mkdir -p "$OUT_DIR/fcstd" "$OUT_DIR/dxf" "$OUT_DIR/svg"

# ── 5. Start freecad-mcp in the background ────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 3 — Starting freecad-mcp${NC}"

MCP_LOG="$SCRIPT_DIR/freecad_mcp.log"

# Kill any previous freecad-mcp process (best-effort)
pkill -f "freecad-mcp" &>/dev/null || true

uvx freecad-mcp > "$MCP_LOG" 2>&1 &
MCP_PID=$!
ok "freecad-mcp started (PID $MCP_PID) — log: $MCP_LOG"

# Give the MCP server a moment to initialise
sleep 2

# ── 6. Run the generator via FreeCAD headless ─────────────────────────────────
echo ""
echo -e "${BOLD}  Step 4 — Running generate_floorplan.py${NC}"
echo ""

if "$FREECAD_CMD" "$GENERATOR"; then
    GEN_EXIT=0
else
    GEN_EXIT=$?
fi

echo ""
if [[ $GEN_EXIT -ne 0 ]]; then
    err "generate_floorplan.py exited with code $GEN_EXIT."
    warn "Check the FreeCAD console output above for details."
    echo ""
    warn "Common fixes:"
    echo "    • Make sure FreeCAD GUI is also open (some DXF modules require it)."
    echo "    • See docs/HOW_TO_RUN.txt for the GUI-based workflow."
    exit $GEN_EXIT
fi

# ── 7. Success summary ────────────────────────────────────────────────────────
echo ""
sep
echo -e "  ${GREEN}${BOLD}Done!${NC}  Output files:"
sep
echo ""

FLOORS=( F0 F1 F2 F3 F4 )
for F in "${FLOORS[@]}"; do
    FCSTD="$OUT_DIR/fcstd/floorplan_${F}.FCStd"
    DXF="$OUT_DIR/dxf/floorplan_${F}.dxf"
    SVG="$OUT_DIR/svg/freecad_${F}.svg"
    if [[ -f "$FCSTD" ]]; then
        echo "  $F   FCStd  $FCSTD"
    fi
    if [[ -f "$DXF" ]]; then
        echo "       DXF    $DXF"
    fi
    if [[ -f "$SVG" ]]; then
        echo "       SVG    $SVG"
    fi
done

FULL_3D="$OUT_DIR/fcstd/tubehouse_full_3d.FCStd"
FULL_DXF="$OUT_DIR/dxf/tubehouse_full_3d.dxf"
if [[ -f "$FULL_3D" ]]; then
    echo ""
    echo "  Full 3D  FCStd  $FULL_3D"
fi
if [[ -f "$FULL_DXF" ]]; then
    echo "           DXF    $FULL_DXF"
fi

echo ""
echo "  Open any .FCStd in FreeCAD to inspect the model."
echo "  Open any .dxf in LibreCAD or https://sharecad.org to verify."
echo ""

echo ""
sep
echo ""
