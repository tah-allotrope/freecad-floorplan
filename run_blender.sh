#!/usr/bin/env bash
# run_blender.sh — one-click runner for the Blender visualization pipeline
# ---------------------------------------------------------------------------
# What this script does:
#   1. Checks that Blender is available on PATH.
#   2. Runs setup_blender_scene.py to import OBJ and assemble the scene.
#   3. Runs render_blender.py to produce a Cycles render.
#
# Prerequisites:
#   - Blender 3.6+ or 4.x installed and on PATH
#   - FreeCAD OBJ exports in output/obj/ (run run.sh first)
#
# Usage:
#   chmod +x run_blender.sh
#   ./run_blender.sh

set -euo pipefail

BOLD='\033[1m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

ok()   { echo -e "  ${GREEN}✓${NC}  $*"; }
warn() { echo -e "  ${YELLOW}!${NC}  $*"; }
err()  { echo -e "  ${RED}✗${NC}  $*"; }
sep()  { echo "──────────────────────────────────────────────────────────────"; }

echo ""
echo -e "${BOLD}  Tubehouse — Blender Visualization Pipeline${NC}"
sep

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OBJ_FILE="$SCRIPT_DIR/output/obj/tubehouse_full_3d.obj"
STL_FILE="$SCRIPT_DIR/output/stl/tubehouse_full_3d.stl"
BLEND_FILE="$SCRIPT_DIR/output/blend/tubehouse_scene.blend"
RENDER_OUTPUT="$SCRIPT_DIR/output/png/tubehouse_blender_render.png"

# ── 1. Find Blender ──────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 1 — Checking for Blender${NC}"

BLENDER_CMD="${BLENDER_CMD:-}"

if [[ -z "$BLENDER_CMD" ]]; then
    CANDIDATES=(
        "blender"
        "blender.exe"
        "/usr/bin/blender"
        "/usr/local/bin/blender"
        "/snap/bin/blender"
        "/Applications/Blender.app/Contents/MacOS/blender"
        "C:/Program Files/Blender Foundation/Blender 4.1/blender.exe"
        "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe"
        "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe"
    )

    for candidate in "${CANDIDATES[@]}"; do
        if command -v "$candidate" &>/dev/null 2>&1; then
            BLENDER_CMD="$candidate"
            break
        fi
        if [[ -f "$candidate" ]]; then
            BLENDER_CMD="$candidate"
            break
        fi
    done
fi

if [[ -z "$BLENDER_CMD" ]]; then
    err "Blender not found on PATH or common locations."
    echo ""
    echo "  Install Blender:  https://www.blender.org/download/"
    echo "  Verify:            blender --version"
    echo "  Or set:            BLENDER_CMD=/path/to/blender ./run_blender.sh"
    echo ""
    sep
    exit 1
fi

ok "Blender found: $BLENDER_CMD"

# ── 2. Check OBJ input ───────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 2 — Checking geometry input${NC}"

IMPORT_SOURCE=""
if [[ -f "$OBJ_FILE" ]]; then
    ok "OBJ found: $OBJ_FILE"
    IMPORT_SOURCE="$OBJ_FILE"
elif [[ -f "$STL_FILE" ]]; then
    warn "OBJ not found, falling back to STL: $STL_FILE"
    IMPORT_SOURCE="$STL_FILE"
else
    err "No geometry found. Run ./run.sh first to generate FreeCAD outputs."
    echo ""
    echo "  Expected: $OBJ_FILE"
    echo "  Fallback: $STL_FILE"
    echo ""
    sep
    exit 1
fi

# ── 3. Assemble Blender scene ────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 3 — Assembling Blender scene${NC}"
echo ""

mkdir -p "$SCRIPT_DIR/output/blend"
mkdir -p "$SCRIPT_DIR/output/png"

if "$BLENDER_CMD" --background --python "$SCRIPT_DIR/src/setup_blender_scene.py"; then
    ok "Scene assembled successfully"
else
    err "Scene assembly failed."
    echo "  Check the Blender console output above for details."
    exit 1
fi

# ── 4. Render ─────────────────────────────────────────────────────────────────
echo ""
echo -e "${BOLD}  Step 4 — Cycles render${NC}"
echo ""

RENDER_FLAG="${BLENDER_RENDER:-1}"

if [[ "$RENDER_FLAG" == "1" ]] && [[ -f "$BLEND_FILE" ]]; then
    if "$BLENDER_CMD" --background "$BLEND_FILE" --python "$SCRIPT_DIR/src/render_blender.py"; then
        ok "Render complete"
    else
        err "Render failed."
        echo "  You can open the .blend file manually in Blender to render."
        exit 1
    fi
elif [[ "$RENDER_FLAG" != "1" ]]; then
    warn "Render skipped (BLENDER_RENDER=${RENDER_FLAG})"
else
    err "Blend file not found: $BLEND_FILE"
    exit 1
fi

# ── 5. Summary ───────────────────────────────────────────────────────────────
echo ""
sep
echo -e "  ${GREEN}${BOLD}Done!${NC}  Blender outputs:"
sep
echo ""

if [[ -f "$BLEND_FILE" ]]; then
    echo "  Scene   $BLEND_FILE"
fi
if [[ -f "$RENDER_OUTPUT" ]]; then
    echo "  Render  $RENDER_OUTPUT"
fi

echo ""
echo "  Open the .blend file in Blender to explore or adjust the scene."
echo ""