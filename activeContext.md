# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** Generate a 4×25m five-storey tube-house from `spec/floorplan-spec.json` using FreeCAD, then export to Blender for presentation-quality rendering.

## Current Task Plan
- [x] PHASE-01: OBJ export adapter (`src/blender_export_utils.py`)
- [x] PHASE-02: Blender scene setup, materials, render script
- [x] PHASE-03: Batch runner integration, final verification

## Completed Work

### PHASE-01 — OBJ Export Adapter
- Created `src/blender_export_utils.py` with per-floor OBJ export (`export_floor_obj`) and combined OBJ export (`export_combined_obj`), named group conventions, MTL material palette, and convention-based material inference.
- Created `tests/test_blender_export_utils.py` (12 pure-Python tests).
- Integrated OBJ export into `src/generate_floorplan.py`: added `OUT_OBJ`, `OUT_BLEND` constants, `ensure_output_dirs()` entries, and export calls in `draw_floor()` and `stack_floors()`.

### PHASE-02 — Blender Scene Setup
- Created `src/blender_materials.py` with 10 PBR materials (Principled BSDF), room/zone/OBJ-group material maps, `create_blender_material()` and `create_all_materials()`.
- Created `spec/blender_materials.json` sidecar config for data-driven material assignment, lighting, camera, and render settings.
- Created `src/setup_blender_scene.py`: import OBJ (STL fallback), assign materials by convention + config, add sun/fill lights, camera targeting bounding box center, save `.blend`.
- Created `src/render_blender.py`: headless Cycles render (1920×1080, 128 samples, configurable).
- Created `run_blender.sh`: one-command batch runner (find Blender, check OBJ, assemble scene, render).
- Created `tests/test_blender_materials.py` (16 tests including JSON/Python consistency).

### PHASE-03 — Batch Runner Integration
- Updated `run.sh` to create `output/obj/` and `output/blend/` directories, and to display OBJ/MTL outputs in the success summary.
- Added a hint in `run.sh` to run `./run_blender.sh` for the visualization pipeline.
- Both `run.sh` (FreeCAD) and `run_blender.sh` (Blender) are now separate one-command runners per the plan's grill-me default.

## File Inventory
| File | Purpose |
|------|---------|
| `src/generate_floorplan.py` | FreeCAD generation (floors, stacked model, facade, exports) |
| `src/floorplan_utils.py` | Pure helpers for floor height math |
| `src/facade_utils.py` | Pure helpers for facade data |
| `src/blender_export_utils.py` | OBJ/MTL export from FreeCAD |
| `src/blender_materials.py` | PBR material palette, room/zone maps |
| `src/setup_blender_scene.py` | Blender scene assembly (OBJ import, materials, lights, camera) |
| `src/render_blender.py` | Headless Cycles render |
| `spec/blender_materials.json` | Data-driven Blender config (materials, lighting, camera, render) |
| `spec/floorplan-spec.json` | Source of truth for all geometry |
| `run.sh` | FreeCAD batch runner |
| `run_blender.sh` | Blender visualization runner |
| `tests/test_floorplan_utils.py` | Floor height math tests |
| `tests/test_facade_utils.py` | Facade feature tests |
| `tests/test_blender_export_utils.py` | OBJ export helper tests |
| `tests/test_blender_materials.py` | Material palette and JSON consistency tests |
| `plans/2026-05-08-blender-integration-plan.md` | Three-phase integration plan |
| `reports/2026-05-08-phase-01-obj-export.html` | Phase 01 report |
| `reports/2026-05-08-phase-02-blender-scene-setup.html` | Phase 02 report |

## Verification
- All 35 pure-Python tests pass: `python -m unittest discover -s tests -v`
- All source files compile clean: `python -m py_compile src/*.py`
- FreeCAD runtime not available locally; Blender runtime not available locally
- OBJ export, Blender scene setup, and render scripts are structurally complete and await runtime validation

## Outstanding
1. Install FreeCAD or expose `freecadcmd` on PATH to validate generation + OBJ export
2. Install Blender on PATH to validate scene assembly + Cycles render
3. If PDF export is required, ensure `cairosvg` is available in the FreeCAD Python environment
4. Visual iteration on materials and camera framing once renders are available