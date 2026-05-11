---
title: "Upgrade OBJ Pipeline and Add IFC Export"
date: 2026-05-11
status: "draft"
request: "Multi-phase plan based on floorplan-to-3D workflow research: improve OBJ quality, add glTF, add IFC via IfcOpenShell, migrate to FreeCAD Arch workbench"
plan_type: "multi-phase"
research_inputs:
  - "research/2026-05-11_freecad-blender-floorplan-3d-workflow.md"
  - "research/2026-05-11_freecad-blender-floorplan-3d-workflow-landscape.md"
---

# Plan: Upgrade OBJ Pipeline and Add IFC Export

## Objective

Upgrade the existing FreeCAD-to-Blender visualization pipeline with three incremental phases: (1) fix OBJ mesh quality and improve Blender renders, (2) add parallel IFC4 export using IfcOpenShell's Python API, and (3) migrate FreeCAD geometry generation to Arch/BIM workbench objects for proper wall openings and native IFC round-tripping. Each phase delivers standalone value and can ship independently.

## Context Snapshot

- **Current state:** Working OBJ→MTL→Blender→Cycles pipeline producing 1920x1080 renders. FreeCAD uses raw `Part::Box` primitives (no Arch/BIM, no IFC, no 3D window/door geometry). OBJ has no normals, includes 2D wires, and uses fragile keyword-based material inference.
- **Desired state:** Clean OBJ with normals and filtered 2D objects; parallel IFC4 export readable by Bonsai/BlenderBIM; optionally, FreeCAD Arch objects with proper wall openings and hosted windows/doors.
- **Key repo surfaces:** `src/generate_floorplan.py`, `src/blender_export_utils.py`, `src/blender_materials.py`, `src/setup_blender_scene.py`, `src/render_blender.py`, `spec/floorplan-spec.json`, `spec/blender_materials.json`, `tests/test_blender_export_utils.py`, `tests/test_blender_materials.py`
- **Out of scope:** Blender Geometry Nodes pipeline, FBX export, USD export, real-time web viewer, CairoSVG/PDF fixes, roof geometry generation.

## Research Inputs

- `research/2026-05-11_freecad-blender-floorplan-3d-workflow.md` — Domain and codebase analysis identifying: (1) OBJ lacks normals/UVs, exports 2D wire pollution; (2) No IFC export exists; (3) IfcOpenShell Python API can generate IFC4 directly from spec JSON without FreeCAD Arch objects; (4) Bonsai v0.8.5+ provides full IFC authoring in Blender.
- `research/2026-05-11_freecad-blender-floorplan-3d-workflow-landscape.md` — Detailed codebase audit confirming `Part::Box` wall primitives, OBJ group convention mapping, 3-tier material system, and the recommended phased upgrade path. Identifies IfcOpenShell API patterns for creating IfcProject/IfcSite/IfcBuilding/IfcBuildingStorey/IfcWall hierarchy.

## Assumptions and Constraints

- **ASM-001:** `ifcopenshell` Python package is installable via `pip install ifcopenshell` and is pure-Python + compiled wheels available on PyPI. No FreeCAD dependency needed for IFC generation.
- **ASM-002:** The `spec/floorplan-spec.json` schema contains enough data (wall x/y/w/h/thickness, door positions/widths, room names/zones) to drive IFC wall and opening creation without schema changes.
- **ASM-003:** Blender 4.1.1 (currently installed) supports `bpy.ops.wm.obj_import` and will support `bpy.ops.export_scene.gltf` for future glTF export.
- **CON-001:** IFC export must be a parallel path, not a replacement for OBJ. The existing OBJ→Blender→Cycles pipeline must keep working.
- **CON-002:** All pure-Python logic must remain testable via `python -m unittest discover -s tests -v` without FreeCAD or Blender installed.
- **DEC-001:** Phase 2 IFC generation uses IfcOpenShell Python API directly from spec JSON, independent of FreeCAD's geometry. This avoids requiring Arch workbench changes to get IFC output.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Fix OBJ mesh quality and improve Blender render | None | `src/blender_export_utils.py` (normals, 2D filter), `src/setup_blender_scene.py` (ground plane, HDRI) |
| PHASE-02 | Add IFC4 export from spec JSON via IfcOpenShell | None | `src/ifc_export_utils.py`, `tests/test_ifc_export_utils.py` |
| PHASE-03 | Migrate FreeCAD walls to Arch API with hosted openings | PHASE-01, PHASE-02 | Updated `src/generate_floorplan.py` using `Arch.makeWall()`, `Arch.makeWindowPreset()` |

## Detailed Phases

### PHASE-01 - Fix OBJ Mesh Quality and Blender Render Improvements

**Goal**
Repair known deficiencies in the OBJ export pipeline and improve the Blender render with ground plane, HDRI environment, and better camera framing.

**Tasks**
- [ ] TASK-01-01: Add face normal computation to `export_floor_obj()` and `export_combined_obj()` in `src/blender_export_utils.py`. Compute per-face normals from cross product of edge vectors and write `vn` lines + `f v//vn` format in OBJ output.
- [ ] TASK-01-02: Add a `filter_3d_only` parameter to OBJ export functions that skips objects whose `Shape` has zero volume (i.e., 2D wires, lines, dimensions, text). Check `obj.Shape.Volume > 0` or `obj.Shape.Solids` non-empty before including in export.
- [ ] TASK-01-03: Add mm→m scale conversion option to OBJ export. Default to writing coordinates in meters (divide by 1000) to match Blender's unit system. Add `scale_factor` parameter (default 0.001) with corresponding MTL `# units: meters` comment.
- [ ] TASK-01-04: Update `src/setup_blender_scene.py` to add a ground plane mesh (a large flat plane at Z=0) with a `Ground_Concrete` material assignment.
- [ ] TASK-01-05: Update `src/setup_blender_scene.py` to add an HDRI environment texture node in the World shader. Load from `spec/blender_materials.json` `environment.hdri_path` if present, otherwise use a neutral grey world background at increased strength.
- [ ] TASK-01-06: Update `spec/blender_materials.json` to add `environment` section with `hdri_path` (nullable), `background_color`, and `background_strength` fields. Add `ground_plane` section with `size`, `material` fields.
- [ ] TASK-01-07: Add unit tests for normal computation and 2D object filtering in `tests/test_blender_export_utils.py`. Test that face normals are unit-length and consistently oriented. Test that filter function excludes objects with `Shape.Volume == 0`.
- [ ] TASK-01-08: Run `python -m unittest discover -s tests -v` and `python -m py_compile src/*.py` to verify.

**Files / Surfaces**
- `src/blender_export_utils.py` — Add normal computation, 2D filter, scale factor
- `src/setup_blender_scene.py` — Add ground plane, HDRI environment
- `spec/blender_materials.json` — Add environment and ground config
- `tests/test_blender_export_utils.py` — New test cases for normals and filtering

**Dependencies**
- None (works with current FreeCAD and Blender installations)

**Exit Criteria**
- [ ] OBJ exports include `vn` normal lines and `f v//vn` face references
- [ ] OBJ exports exclude 2D-only objects (lines, dimensions, text)
- [ ] `python -m unittest discover -s tests -v` passes all tests including new ones
- [ ] `python -m py_compile src/blender_export_utils.py src/setup_blender_scene.py` succeeds
- [ ] Cycles render includes ground plane and improved lighting

**Phase Risks**
- **RISK-01-01:** FreeCAD's `Mesh` module may not produce correctly oriented normals for all shape types. Mitigation: test with the actual spec and verify normals in Blender's viewport with face orientation overlay.
- **RISK-01-02:** HDRI files are not bundled in the repo. Mitigation: make HDRI path optional in JSON, fall back to solid grey environment.

### PHASE-02 - Add IFC4 Export via IfcOpenShell

**Goal**
Create a pure-Python IFC4 export module that reads `spec/floorplan-spec.json` and produces a valid `.ifc` file with IfcProject/IfcSite/IfcBuilding/IfcBuildingStorey/IfcWall hierarchy, without requiring FreeCAD's Arch workbench.

**Tasks**
- [ ] TASK-02-01: Add `ifcopenshell` to project dependencies (create or update `requirements.txt` with `ifcopenshell>=0.7`). Verify it installs cleanly alongside FreeCAD's Python.
- [ ] TASK-02-02: Create `src/ifc_export_utils.py` with the following public API:
  - `create_ifc_project(spec: dict) -> ifcopenshell.file:` — Create IfcProject, IfcSite, IfcBuilding from spec metadata (plot width/depth, project name)
  - `create_ifc_storeys(model, spec: dict) -> list:` — Create IfcBuildingStorey per floor, with correct elevation from `floorplan_utils.cumulative_floor_offsets()`
  - `create_ifc_walls(model, spec: dict, storeys: list) -> list:` — Create IfcWall per wall definition, positioned at correct (x, y) with height from floor spec and thickness from wall data
  - `create_ifc_spaces(model, spec: dict, storeys: list) -> list:` — Create IfcSpace per room with name and area
  - `export_ifc(spec: dict, output_path: str) -> str:` — Top-level function that orchestrates the above and writes the `.ifc` file
- [ ] TASK-02-03: Map spec JSON wall data to IfcOpenShell API calls. Each wall in `spec["floors"][i]["walls"]` has `x, y, w, h` (plus thickness from `wall_thickness` or a default 200mm). Map these to `ifcopenshell.api.geometry.add_wall_representation()`.
- [ ] TASK-02-04: Map spec JSON room data to IfcSpace. Each room in `spec["floors"][i]["rooms"]` has `id, name, x, y, w, h`. Create bounded IfcSpace elements with name and `GrossFloorArea` quantity.
- [ ] TASK-02-05: Map spec JSON door data to IfcDoor placeholder elements (position markers without 3D geometry initially). Each door has `x, y, width, type`. Create IfcDoor with `OverallWidth` and position within the correct storey.
- [ ] TASK-02-06: Create `tests/test_ifc_export_utils.py` with pure-Python tests that:
  - Verify IFC file is valid by reading it back with `ifcopenshell.open()`
  - Assert correct number of IfcBuildingStorey elements (5)
  - Assert correct number of IfcWall elements (counts from spec)
  - Assert IfcProject and IfcSite exist
  - Assert storey elevations match `cumulative_floor_offsets()`
  - These tests must work without FreeCAD installed
- [ ] TASK-02-07: Integrate IFC export into `src/generate_floorplan.py` by adding `OUT_IFC` output directory constant, `ensure_output_dirs()` entry, and conditional export triggered by `env_flag("EXPORT_IFC")` in `main()`. Add IFC output to `run.sh` summary.
- [ ] TASK-02-08: Run `python -m unittest discover -s tests -v` and `python -m py_compile src/ifc_export_utils.py`.

**Files / Surfaces**
- `src/ifc_export_utils.py` — New module: IFC4 generation from spec JSON
- `src/generate_floorplan.py` — Add IFC export integration (new `OUT_IFC` dir, env flag, summary display)
- `tests/test_ifc_export_utils.py` — New: IFC validity and content tests
- `requirements.txt` — New or updated: add `ifcopenshell>=0.7`
- `run.sh` — Add IFC output display to summary section

**Dependencies**
- None (IfcOpenShell is pure-Python, independent of FreeCAD and Blender)

**Exit Criteria**
- [ ] `python -m unittest discover -s tests -v` passes all tests including new IFC tests
- [ ] Running with `EXPORT_IFC=1` produces a valid `.ifc` file in `output/ifc/`
- [ ] The IFC file can be opened in Bonsai/BlenderBIM or Solibri and shows 5 storeys, walls, and rooms
- [ ] IFC export does not break existing OBJ/STL/DXF/SVG pipeline

**Phase Risks**
- **RISK-02-01:** IfcOpenShell wheel availability on Windows may require conda or special install. Mitigation: test `pip install ifcopenshell` on the Windows machine; conda-forge is a fallback.
- **RISK-02-02:** Spec JSON wall definitions are axis-aligned rectangles without explicit thickness on all walls. Mitigation: use `wall_thickness` from floor defaults (200mm exterior, 100mm interior) and fall back gracefully.

### PHASE-03 - Migrate FreeCAD Geometry to Arch/BIM Workbench

**Goal**
Replace raw `Part::Box` wall generation in `generate_floorplan.py` with FreeCAD `Arch.makeWall()` calls that produce parametric BIM objects with proper IfcClassification, automatic opening subtraction for windows and doors, and native IFC export capability.

**Tasks**
- [ ] TASK-03-01: Create `src/arch_generation.py` with functions:
  - `make_arch_wall(spec_wall, height, floor_elevation) -> Arch Wall:` — Create an Arch wall from spec wall data with correct position, height, width (thickness), and IfcType
  - `make_arch_window(spec_window, host_wall) -> Arch Window:` — Create a window/door hosted in the parent wall with automatic opening subtraction
  - `make_arch_slab(spec_floor, floor_elevation, thickness) -> Arch Structure:` — Create a floor slab from spec data
  - `make_arch_floor(floors, storey_heights) -> list:` — Create IfcBuildingStorey grouping per floor
- [ ] TASK-03-02: Refactor `draw_floor()` in `src/generate_floorplan.py` to call `make_arch_wall()` instead of `Part.makeBox()`. Keep the existing `Part.makeBox()` as a fallback behind `env_flag("USE_ARCH")` for backward compatibility.
- [ ] TASK-03-03: Add 3D window and door geometry using `Arch.makeWindowPreset()` or `Arch.makeWindow()` with `Hosts = [wall]` to automatically subtract openings. Map spec door/window definitions to Arch window types.
- [ ] TASK-03-04: Add `Arch.makeStructure()` for floor slabs instead of the current manual `Part.makeBox()` approach.
- [ ] TASK-03-05: Add NativeIFC export option: when `env_flag("EXPORT_IFC")` is set and Arch objects are present, use FreeCAD's NativeIFC workbench to export the `.ifc` file directly from Arch objects as an alternative to the IfcOpenShell pure-Python approach from Phase 02.
- [ ] TASK-03-06: Create `tests/test_arch_generation.py` — unit tests for the pure-Python helper functions in `arch_generation.py` that validate wall/window/slab parameter extraction from spec JSON without requiring FreeCAD.
- [ ] TASK-03-07: Update `run.sh` to add `USE_ARCH=1` option and document both pipelines (Part::Box fallback vs Arch).
- [ ] TASK-03-08: Run `python -m unittest discover -s tests -v` and `python -m py_compile src/arch_generation.py src/generate_floorplan.py`.

**Files / Surfaces**
- `src/arch_generation.py` — New module: Arch API wrappers for wall/window/slab creation
- `src/generate_floorplan.py` — Major refactor: `draw_floor()` uses Arch API when `USE_ARCH=1`
- `tests/test_arch_generation.py` — New: parameter extraction tests
- `run.sh` — Add `USE_ARCH` env flag documentation
- `activeContext.md` — Update with new pipeline option

**Dependencies**
- PHASE-01 (OBJ quality fixes must not be broken by Arch migration)
- PHASE-02 (IFC export integration in `generate_floorplan.py` must coexist)

**Exit Criteria**
- [ ] `python -m unittest discover -s tests -v` passes all tests
- [ ] Running with `USE_ARCH=1 GENERATE_STACKED=1` produces FCStd files with Arch Wall objects that have IfcType metadata
- [ ] Arch walls have proper 3D geometry with window/door openings subtracted
- [ ] Running with `USE_ARCH=1 EXPORT_IFC=1` produces a valid IFC file from FreeCAD's NativeIFC
- [ ] Running without `USE_ARCH` flag produces identical OBJ output to current behavior (backward compatible)

**Phase Risks**
- **RISK-03-01:** FreeCAD Arch API behavior may differ between version 1.0 and 1.1+. Mitigation: gate Arch features behind `USE_ARCH` env flag so the Part::Box path remains the default.
- **RISK-03-02:** `Arch.makeWindow()` in FreeCAD 1.0 may not support all window types needed (sliding, garage). Mitigation: start with swing doors and fixed windows; add types incrementally.
- **RISK-03-03:** Arch objects may change the OBJ export geometry (walls with openings will have more complex meshes). Mitigation: verify OBJ output visually and update `blender_export_utils.py` group naming if needed.

## Verification Strategy

- **TEST-001:** `python -m unittest discover -s tests -v` must pass all 35+ tests across all phases
- **TEST-002:** `python -m py_compile src/*.py` must succeed for all source modules
- **MANUAL-001:** Open generated `.ifc` file in Bonsai/BlenderBIM and verify 5 storeys, walls, and rooms are visible
- **MANUAL-002:** Render Cycles output with improved OBJ and verify normals render correctly (no faceted shading on flat walls)
- **MANUAL-003:** Open Arch-generated `.FCStd` in FreeCAD GUI and verify walls have IfcType metadata and windows create openings
- **OBS-001:** `pip install ifcopenshell` must succeed on the target machine (Windows, Python 3.x from FreeCAD or system)

## Risks and Alternatives

- **RISK-001:** IfcOpenShell has C++ dependencies that may fail to install on some Windows Python environments. Mitigation: conda-forge provides pre-built wheels; the Phase 02 IFC module can be made optional (graceful import failure).
- **RISK-002:** FreeCAD Arch workbench has known stability issues with complex wall joinery in some configurations. Mitigation: `USE_ARCH` flag keeps Part::Box as default; Arch is opt-in.
- **ALT-001:** Instead of direct IfcOpenShell Python IFC generation (Phase 02), we could generate IFC via FreeCAD's NativeIFC workbench. Rejected for Phase 02 because it requires FreeCAD runtime and Arch objects, but adopted as Phase 03 option for richer IFC output.
- **ALT-002:** Instead of fixing OBJ normals (Phase 01), we could skip OBJ entirely and use only glTF. Rejected because OBJ is the existing working pipeline and glTF from FreeCAD requires additional tooling (IfcConvert or Blender Python export).

## Grill Me

1. **Q-001:** Should Phase 01 also add glTF export as a third output format alongside OBJ and STL?
   - **Recommended default:** No — defer glTF to a future phase. It adds complexity (Blender Python export or IfcConvert dependency) without blocking IFC work.
   - **Why this matters:** glTF would enable web viewers but adds a new export path to maintain.
   - **If answered differently:** Add a TASK-01-09 for glTF export via Blender Python (`bpy.ops.export_scene.gltf`) in the setup scene script.

2. **Q-002:** Should Phase 02's IFC export happen inside `generate_floorplan.py` (triggered by env flag alongside FreeCAD) or as a standalone script (`src/generate_ifc.py`) that reads the spec JSON independently?
   - **Recommended default:** Standalone script (`src/generate_ifc.py`) that can run without FreeCAD, plus integration hook in `generate_floorplan.py`.
   - **Why this matters:** A standalone script is debuggable without FreeCAD and can be tested in CI. The integration hook keeps it in the `run.sh` workflow.
   - **If answered differently:** Embed everything in `generate_floorplan.py` behind `EXPORT_IFC` env flag.

3. **Q-003:** For Phase 03, should the Arch migration replace `Part::Box` walls entirely or keep both paths permanently?
   - **Recommended default:** Keep both paths permanently behind `USE_ARCH=1` env flag. Arch path is opt-in, Part::Box remains default.
   - **Why this matters:** Arch API is less stable than Part::Box across FreeCAD versions. Having both paths provides a fallback.
   - **If answered differently:** Remove Part::Box path after Phase 03 is validated, simplifying long-term maintenance.

No additional clarification questions beyond these three.

## Suggested Next Step

Answer the three Grill Me questions, update this plan with resolved decisions, then begin PHASE-01 implementation. Start with TASK-01-01 (OBJ normals) since it has no dependencies and delivers immediate visual improvement.