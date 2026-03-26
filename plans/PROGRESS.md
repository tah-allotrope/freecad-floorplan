# Tubehouse FreeCAD Project — Progress Report
*Last updated: 21 March 2026*

---

## Project Overview

A **4 m × 25 m Vietnamese tube house (nhà ống)** on a narrow urban lot, designed in 5 storeys.
The workflow is fully code-driven:

```
JSON spec  →  Python script  →  FreeCAD  →  FCStd + DXF + SVG
```

An optional MCP layer lets you talk to FreeCAD conversationally through Claude / opencode:

```
You (natural language)  →  Claude/opencode  →  freecad-mcp  →  FreeCAD (live)
```

The spec-driven approach is best for batch regeneration; the MCP approach is best for interactive tweaks and exploration.

---

## What Was Done This Session

### Floor specs completed (F3 + F4)

All 5 floors are now fully specified in `spec/floorplan-spec.json`.

**F3 — Third Floor** (newly added) includes:
- Front balcony
- Home office (street-facing, good natural light)
- Flex / guest bedroom
- Master suite with dressing room, en-suite bathroom, and rear balcony

**F4 — Rooftop** (newly added) includes:
- Penthouse sky lounge
- Open front terrace and pergola terrace
- Lift machine room + stair head (required services)
- Rooftop garden zone
- Solar panel zone (north-facing for Vietnam)

### Code additions

**`src/generate_floorplan.py`** — `stack_floors()` function added.
Loops through all floor specs, calls `draw_floor()` for each, then assembles a single combined 3D document (`tubehouse_full_3d.FCStd`) with every floor offset to its correct Z height (default 3.2 m per storey). Also exports a combined DXF.

**`src/freecad_session_starter.py`** — new session helper script.
Prints a human-readable project summary (floor names, room counts, zone depths, total building height), checks whether the FreeCAD RPC listener is reachable on `localhost:9876` by default, and prints the `opencode.json` snippet you need to enable the MCP connector. Run it with `python src/freecad_session_starter.py` before starting a FreeCAD session to orient yourself quickly.

**`run.sh`** — one-click shell script.
Checks for FreeCAD and `uv`, starts `freecad-mcp` in the background, runs the generator headless via `freecadcmd`, and prints a final summary of every output file. If prerequisites are missing it prints clear setup instructions rather than crashing. Usage: `chmod +x run.sh && ./run.sh`.

**`plans/tubehouse-freecad-mcp-workflow.md`** — comprehensive beginner workflow guide.
Covers the MCP architecture, available tools, step-by-step workflow for both the script approach and the interactive MCP approach, troubleshooting tips, and a glossary of FreeCAD terms for newcomers.

---

## Current State

### Floor spec coverage

| Floor | Name | Spec | FCStd | DXF | SVG |
|-------|------|------|-------|-----|-----|
| F0 | Ground Floor | ✅ | ✅ | ✅ | ✅ |
| F1 | First Floor | ✅ | ✅ | ✅ | ✅ |
| F2 | Second Floor | ✅ | ✅ | ✅ | ✅ |
| F3 | Third Floor | ✅ | ✗ needs FreeCAD | ✗ | ✗ |
| F4 | Rooftop | ✅ | ✗ needs FreeCAD | ✗ | ✗ |
| Full 3D stack | All floors | ✅ | ✗ needs FreeCAD | ✗ | — |

All 5 floors are **specced**. F0–F2 have been generated and output files exist. F3, F4, and the full 3D stack are ready to generate — they just need FreeCAD to run the script.

### What currently exists in `output/`

- `output/fcstd/` — FreeCAD project files for F0, F1, F2
- `output/dxf/` — DXF drawings for F0, F1, F2 (can be opened in LibreCAD or https://sharecad.org)
- `output/svg/` — SVG previews for F0, F1, F2

### What still needs FreeCAD running to produce

- `output/fcstd/floorplan_F3.FCStd` and `floorplan_F4.FCStd`
- `output/dxf/floorplan_F3.dxf` and `floorplan_F4.dxf`
- `output/svg/freecad_F3.svg` and `freecad_F4.svg`
- `output/fcstd/tubehouse_full_3d.FCStd` — the complete 5-storey massing
- `output/dxf/tubehouse_full_3d.dxf` — combined DXF for all floors

---

## Suggested Next Steps

### 1. Get FreeCAD installed and test the MCP connection
Download FreeCAD from https://www.freecad.org/downloads.php and install `uv` (`curl -LsSf https://astral.sh/uv/install.sh | sh` on macOS/Linux). Then run:
```
python src/freecad_session_starter.py   # check connection status
./run.sh                                 # one-click full generate
```
The session starter will tell you whether the MCP server is reachable before you start.

### 2. Run the full 5-floor stack
Once FreeCAD is running, open the Python console and execute:
```python
exec(open(r'src/generate_floorplan.py').read())
stack_floors(spec['floors'])
```
This will generate F3 and F4 output files and produce the combined `tubehouse_full_3d.FCStd` showing all floors stacked to their correct height.

### 3. Facade and window detailing
The spec supports `window` elements (already wired up in the drawing code) but F3 and F4 don't have window coordinates yet. The next design pass should add street-facing windows for F3 (home office glazing) and F4 (sky lounge), and specify balcony railings.

### 4. Structural and MEP considerations for Vietnam's tropical climate
A few things worth thinking about before the design is locked:

- **Ventilation** — cross-ventilation is important in a narrow tube house. The light wells on both sides are a good start; consider whether F3 and F4 openings align with the prevailing breeze direction.
- **Solar shading** — deep overhangs or louvres on the south-facing facade will reduce heat gain significantly in a tropical urban location.
- **Rooftop solar zone** (already in F4 spec) — confirm roof structural capacity for panel load and plan cable runs down through the lift shaft.
- **Foundation** — a 4 m × 25 m footprint on an urban lot will likely need bored piles; worth flagging to a structural engineer early.
- **MEP shaft** — the lift shaft and staircase core already doubles as a MEP route; confirm plumbing stack and electrical risers fit within the `CORE VOID` space.

### 5. Potential next integrations

- **BIM export (IFC)** — FreeCAD's BIM workbench can export IFC files for sharing with structural or MEP engineers.
- **Structural analysis** — tools like CalculiX (built into FreeCAD) or OpenSees can do basic frame analysis once the 3D model is clean.
- **Quantity take-off** — the JSON spec already has all room areas; a small Python script could auto-generate a basic schedule of areas and wall lengths.

---

*The project is in good shape — all floors are designed, the tooling is in place, and the next session just needs FreeCAD up and running to bring the full building to life.*
