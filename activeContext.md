# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** Generate a 4x25m five-storey tube-house from `spec/floorplan-spec.json` using FreeCAD, then export to Blender for presentation-quality rendering.

## Current Task Plan
- [x] PHASE-01: OBJ export adapter (`src/blender_export_utils.py`)
- [x] PHASE-02: Blender scene setup, materials, render script
- [x] PHASE-03: Batch runner integration, final verification
- [x] PHASE-04: End-to-end runtime validation (FreeCAD + Blender)

## Completed Work

### PHASE-01 — OBJ Export Adapter
- Created `src/blender_export_utils.py` with per-floor OBJ export (`export_floor_obj`) and combined OBJ export (`export_combined_obj`), named group conventions, MTL material palette, and convention-based material inference.
- Created `tests/test_blender_export_utils.py` (12 pure-Python tests).
- Integrated OBJ export into `src/generate_floorplan.py`: added `OUT_OBJ`, `OUT_BLEND` constants, `ensure_output_dirs()` entries, and export calls in `draw_floor()` and `stack_floors()`.

### PHASE-02 — Blender Scene Setup
- Created `src/blender_materials.py` with 10 PBR materials (Principled BSDF), room/zone/OBJ-group material maps, `create_blender_material()` and `create_all_materials()`.
- Created `spec/blender_materials.json` sidecar config for data-driven material assignment, lighting, camera, and render settings.
- Created `src/setup_blender_scene.py`: import OBJ (STL fallback), assign materials by convention + config, add sun/fill lights, camera targeting bounding box center, save `.blend`.
- Created `src/render_blender.py`: headless Cycles render (1920x1080, 128 samples, configurable).
- Created `run_blender.sh`: one-command batch runner (find Blender, check OBJ, assemble scene, render).
- Created `tests/test_blender_materials.py` (16 tests including JSON/Python consistency).

### PHASE-03 — Batch Runner Integration
- Updated `run.sh` to create `output/obj/` and `output/blend/` directories, and to display OBJ/MTL outputs in the success summary.
- Added a hint in `run.sh` to run `./run_blender.sh` for the visualization pipeline.

### PHASE-04 — End-to-End Runtime Validation (2026-05-09)
- Installed Blender 4.1.1 at `C:\Users\tukum\Blender\blender-4.1.1-windows-x64\blender.exe`
- Found FreeCAD 1.0.2 at `C:\Users\tukum\AppData\Local\Programs\FreeCAD 1.0\bin\freecadcmd.exe`
- Generated all 5 floors (F0-F4) + stacked 3D model + facade via `freecadcmd` with `GENERATE_STACKED=1 GENERATE_FACADE=1 EXPORT_ARCHITECT_PACKAGE=1`
- Fixed Blender 4.x API compatibility issues:
  - `bpy.ops.import_scene.obj` -> `bpy.ops.wm.obj_import` (Blender 4.x OBJ import API)
  - `bpy.ops.import_mesh.stl` -> `bpy.ops.wm.stl_import` (Blender 4.x STL import API)
  - `mat.blend_method = "ALPHA"` -> `"BLEND"` (EEVEE blend mode renamed)
  - `bsdf.inputs["Transmission"]` -> `bsdf.inputs.get("Transmission Weight") or bsdf.inputs.get("Transmission")` (Principled BSDF v2 input rename)
  - `cycles.debug_bvh_type = "AUTO"` -> `"DYNAMIC_BVH"` (Blender 4.x removed AUTO, only DYNAMIC_BVH/STATIC_BVH)
  - Fixed `import_stl()` bug: `l_path` -> `stl_path`
- Assembled Blender scene: `output/blend/tubehouse_scene.blend` (0.78 MB)
- Rendered Cycles output: `output/png/tubehouse_blender_render.png` (712 KB, 1920x1080, 128 samples)
- All 35 tests pass; all `py_compile` checks pass

## Generated Artifacts
| Artifact | Size | Path |
|----------|------|------|
| Combined 3D model | 101 KB | `output/fcstd/tubehouse_full_3d.FCStd` |
| Combined OBJ | 3.2 KB | `output/obj/tubehouse_full_3d.obj` |
| Combined MTL | 0.7 KB | `output/obj/tubehouse.mtl` |
| Combined STL | 61 KB | `output/stl/tubehouse_full_3d.stl` |
| Facade FCStd | 20 KB | `output/fcstd/front_facade_elevation.FCStd` |
| Per-floor OBJ/MTL | ~3.5 KB ea | `output/obj/floorplan_F0-F4.obj` |
| Per-floor FCStd | 74-92 KB ea | `output/fcstd/floorplan_F0-F4.FCStd` |
| Per-floor DXF | 16-23 KB ea | `output/dxf/floorplan_F0-F4.dxf` |
| Blender scene | 0.78 MB | `output/blend/tubehouse_scene.blend` |
| Cycles render | 712 KB | `output/png/tubehouse_blender_render.png` |
| Manifest | 1.3 KB | `output/architect_package_manifest.json` |

## Key Technical Details
- FreeCAD headless: `freecadcmd -c "import sys; sys.path.insert(0, r'path\src'); import generate_floorplan; generate_floorplan.main()"`
  - Direct `freecadcmd script.py` doesn't propagate env vars or print output properly on Windows
  - The SCRIPT_DIR fallback in `generate_floorplan.py` has a hardcoded old path; must use `-c` with import approach
- Blender 4.1.1 on Windows: `blender.exe --background --python script.py` works for both setup and render
- FreeCAD 1.0.2: `freecadcmd.exe` located at `C:\Users\tukum\AppData\Local\Programs\FreeCAD 1.0\bin\freecadcmd.exe`

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

## Verification
- All 35 pure-Python tests pass: `python -m unittest discover -s tests -v`
- All source files compile clean: `python -m py_compile src/*.py`
- FreeCAD generation validated: all 5 floors + stacked 3D + facade + OBJ/MTL/STL/DXF exported
- Blender scene assembly validated: .blend file created with materials, lights, camera
- Cycles render validated: 1920x1080 PNG output at 128 samples

## Outstanding
1. PDF export needs `cairosvg` in FreeCAD Python environment
2. Facade SVG export failed (headless mode, no FreeCADGui) — needs GUI session
3. Visual iteration on materials and camera framing for better renders
4. The `generate_floorplan.py` SCRIPT_DIR fallback path is hardcoded to old `freecad-floorplan` — should be updated or removed