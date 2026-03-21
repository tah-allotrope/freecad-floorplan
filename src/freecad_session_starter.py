#!/usr/bin/env python3
"""
freecad_session_starter.py
==========================
Quick-start helper for the 4×25m Tubehouse FreeCAD project.

What it does
------------
1. Loads the floorplan JSON spec and prints a human-readable summary
   (floor names, room counts, zone depths, total building height).
2. Checks whether the FreeCAD RPC listener is reachable (default:
   localhost:9876). Prints a clear status message whether FreeCAD is ready
   for the MCP bridge - it never crashes on a missing server.
3. Prints the opencode.json snippet you need to enable the freecad MCP
   connector, ready to copy-paste.

Usage
-----
    python src/freecad_session_starter.py

    # Override the spec path or FreeCAD RPC host/port:
    SPEC_FILE=/path/to/floorplan-spec.json RPC_PORT=9876 python src/freecad_session_starter.py
"""

import json
import os
import socket
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from floorplan_utils import total_building_height_mm

# ── Locate project files ─────────────────────────────────────────────────────
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir))
SPEC_FILE = os.environ.get(
    "SPEC_FILE",
    os.path.join(PROJECT_DIR, "spec", "floorplan-spec.json"),
)
RPC_HOST = os.environ.get("RPC_HOST", "localhost")
RPC_PORT = int(os.environ.get("RPC_PORT", 9876))

# ── Helpers ───────────────────────────────────────────────────────────────────

DIVIDER = "-" * 60


def _section(title):
    print(f"\n{DIVIDER}")
    print(f"  {title}")
    print(DIVIDER)


def _try_freecad_connection(host, port, timeout=2.0):
    """Return True if a TCP connection to host:port succeeds within *timeout* s."""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except (ConnectionRefusedError, OSError):
        return False


# ── 1. Load spec ─────────────────────────────────────────────────────────────

_section("Loading spec")

if not os.path.isfile(SPEC_FILE):
    print(f"  ERROR: spec file not found: {SPEC_FILE}")
    sys.exit(1)

with open(SPEC_FILE, encoding="utf-8") as fh:
    spec = json.load(fh)

project = spec["project"]
floors = spec["floors"]
wall_cfg = spec.get("wall_thickness", {})

print(f"  Project : {project['name']}")
print(f"  Location: {project['location']}")
print(f"  Date    : {project['date']}  status={project['status']}")
print(f"  Plot    : {project['plot_width_mm']} mm x {project['plot_depth_mm']} mm")
print(
    f"  Floors  : {len(floors)} defined in spec (num_floors={project.get('num_floors', '?')})"
)

# ── 2. Floor summary ─────────────────────────────────────────────────────────

_section("Floor summary")

for floor in floors:
    level = floor["level"]
    name = floor["name"]
    h_mm = floor.get("floor_to_ceiling_mm", 0)
    rooms = floor.get("rooms", [])
    zones = floor.get("zones", [])
    walls = floor.get("walls", [])
    doors = floor.get("doors", [])
    elems = floor.get("elements", [])
    labels = floor.get("labels", [])
    sheet = floor.get("sheet", "-")
    room_names = ", ".join(r["name"] for r in rooms[:4])
    if len(rooms) > 4:
        room_names += f", ... (+{len(rooms) - 4} more)"
    print(
        f"  F{level}  {name:<22}  sheet={sheet}  "
        f"h={h_mm}mm  zones={len(zones)}  rooms={len(rooms)}  "
        f"walls={len(walls)}  doors={len(doors)}  elem={len(elems)}  lbl={len(labels)}"
    )
    print(f"       Rooms: {room_names}")

total_height_mm = total_building_height_mm(floors)
print(
    f"\n  Total building height (floor-to-ceiling sum): {total_height_mm} mm "
    f"= {total_height_mm / 1000:.2f} m"
)
print(
    f"  Wall thicknesses - "
    f"exterior: {wall_cfg.get('exterior_mm', '?')} mm  "
    f"interior H: {wall_cfg.get('interior_horizontal_mm', '?')} mm  "
    f"interior V: {wall_cfg.get('interior_vertical_mm', '?')} mm"
)

# ── 3. Output files ───────────────────────────────────────────────────────────

_section("Expected output files")

out_root = os.path.join(PROJECT_DIR, "output")
for floor in floors:
    lvl = floor["level"]
    fcstd = os.path.join(out_root, "fcstd", f"floorplan_F{lvl}.FCStd")
    dxf = os.path.join(out_root, "dxf", f"floorplan_F{lvl}.dxf")
    svg = os.path.join(out_root, "svg", f"freecad_F{lvl}.svg")
    exist = lambda p: "OK" if os.path.isfile(p) else "--"
    print(f"  F{lvl}  FCStd {exist(fcstd)}  DXF {exist(dxf)}  SVG {exist(svg)}")

full_3d = os.path.join(out_root, "fcstd", "tubehouse_full_3d.FCStd")
full_dxf = os.path.join(out_root, "dxf", "tubehouse_full_3d.dxf")
print(
    f"  Full 3D stacked  FCStd {'OK' if os.path.isfile(full_3d) else '--'}  "
    f"DXF {'OK' if os.path.isfile(full_dxf) else '--'}"
)

# ── 4. FreeCAD RPC readiness check ───────────────────────────────────────────

_section(f"FreeCAD RPC readiness check  ({RPC_HOST}:{RPC_PORT})")

if _try_freecad_connection(RPC_HOST, RPC_PORT):
    print(f"  OK  FreeCAD RPC listener is reachable at {RPC_HOST}:{RPC_PORT}")
    print("     FreeCAD is ready for the stdio `freecad-mcp` bridge to attach.")
else:
    print(f"  XX  FreeCAD RPC listener NOT reachable at {RPC_HOST}:{RPC_PORT}")
    print()
    print("  In FreeCAD, open the MCP Addon workbench and start the RPC server.")
    print()
    print("  Then, in a separate terminal, run:")
    print("      uvx freecad-mcp")
    print()
    print("  opencode talks to `freecad-mcp` over stdio; the bridge then attaches")
    print("  to FreeCAD over RPC. Both pieces must be running.")

# ── 5. opencode config snippet ────────────────────────────────────────────────

_section("opencode.json config snippet  (copy-paste into your project root)")

snippet = {
    "$schema": "https://opencode.ai/config.json",
    "mcp": {
        "freecad": {
            "type": "local",
            "command": ["uvx", "freecad-mcp"],
            "enabled": True,
        }
    },
}
print(json.dumps(snippet, indent=2))
print()
print(f"  The file already exists at: {os.path.join(PROJECT_DIR, 'opencode.json')}")

# ── 6. Quick-start instructions ──────────────────────────────────────────────

_section("Quick-start")

print("  1. Start FreeCAD (GUI or headless).")
print("  2. In a separate terminal:  uvx freecad-mcp")
print("  3. Inside FreeCAD Python console, run the generator:")
print(
    f"       exec(open(r'{os.path.join(SCRIPT_DIR, 'generate_floorplan.py')}').read())"
)
print()
print("  To generate the full stacked 3D model (after individual floors exist):")
print("       stack_floors(spec['floors'])")
print()
print(DIVIDER)
print("  Session starter complete.")
print(DIVIDER)
