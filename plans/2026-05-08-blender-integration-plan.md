---
title: "Blender Integration for Tubehouse Visualization"
date: "2026-05-08"
status: "draft"
request: "Integrate Blender as a downstream visualization and rendering tool for the FreeCAD tubehouse model, based on the research brief in research/2026-04-30_adding-blender-freecad-workflow.md"
plan_type: "multi-phase"
research_inputs:
  - "research/2026-04-30_adding-blender-freecad-workflow.md"
---

# Plan: Blender Integration for Tubehouse Visualization

## Objective
Establish an automated export pipeline from the FreeCAD tubehouse model to Blender for presentation-quality rendering, material application, and lighting. FreeCAD remains the single source of truth for parametric geometry; Blender consumes exported mesh data and adds visualization-only enhancements.

## Context Snapshot
- **Current state:** FreeCAD Python scripts in `src/generate_floorplan.py` generate per-floor `.FCStd` files, a stacked 3D model (`tubehouse_full_3d.FCStd`), a front facade elevation, and export artifacts (DXF, SVG, STL, PDF). No Blender connectivity exists.
- **Desired state:** An automated, reproducible pipeline that exports the tubehouse model from FreeCAD and imports it into a Blender project with sensible default materials, lighting, and camera — enabling EEVEE/Cycles renders without manual Blender setup.
- **Key repo surfaces:**
  - `src/generate_floorplan.py` — primary generation script (draw_floor, stack_floors, draw_front_facade, export_architect_package)
  - `src/floorplan_utils.py` — pure helpers for floor height math
  - `src/facade_utils.py` — pure helpers for facade data
  - `spec/floorplan-spec.json` — source of truth for geometry
  - `run.sh` — batch runner
  - `output/` — generated artifacts
- **Out of scope:**
  - Replacing FreeCAD as the parametric authoring tool
  - BIM/IFC property editing inside Blender
  - Structural analysis or MEP routing in Blender
  - Any changes to the existing floorplan spec or FreeCAD generation logic

## Research Inputs
- `research/2026-04-30_adding-blender-freecad-workflow.md` — Establishes the core principle: FreeCAD for parametric modeling, Blender for downstream rendering. Recommends OBJ or IFC export, with IfcOpenShell as the interoperability backbone. Warns against re-authoring geometry in Blender.

## Assumptions and Constraints
- **ASM-001:** Blender 3.x+ is installed locally or available via command line (`blender` or `blender.exe` on PATH) for headless rendering.
- **ASM-002:** The existing STL export in `generate_floorplan.py` (via `export_document_stl`) produces meshes that Blender can import, but per-object material assignment is lost in STL. OBJ with per-object groups preserves more structure.
- **ASM-003:** The FreeCAD generation pipeline stays untouched — we only add export adapters and Blender scripts, never modifying existing geometry creation.
- **ASM-004:** BlenderBIM is a future enhancement, not part of the initial integration. Starting with OBJ/Wavefront export keeps the dependency surface minimal.
- **CON-001:** Blender headless mode (`blender --background --python script.py`) has no GPU for EEVEE rendering on most CI servers; Cycles CPU rendering is the fallback.
- **CON-002:** The FreeCAD Mesh module must be available for any mesh export beyond STL.
- **DEC-001:** OBJ is chosen as the primary interchange format (not IFC) because it requires no additional Python packages, preserves object grouping, and Blender imports it natively. IFC via IfcOpenShell is a phase-2 enhancement.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | OBJ export adapter in FreeCAD pipeline | None | `src/blender_export_utils.py`, OBJ files per floor + combined |
| PHASE-02 | Blender scene setup script with materials, lighting, and camera | PHASE-01 | `src/setup_blender_scene.py`, `.blend` file |
| PHASE-03 | Batch runner integration and headless render | PHASE-02 | Updated `run.sh`, PNG renders |

## Detailed Phases

### PHASE-01 - OBJ Export Adapter
**Goal**
Add a pure-Python + FreeCAD OBJ export function that produce per-floor and combined OBJ files, preserving object names and grouping for Blender import.

**Tasks**
- [ ] TASK-01-01: Create `src/blender_export_utils.py` with a `export_floor_obj(floor_doc, level, output_dir)` function that exports each named object group (WALLS, ROOMS, STAIRS, SYMBOLS) as a named OBJ group using FreeCAD's `Mesh` module.
- [ ] TASK-01-02: Add `export_combined_obj(stacked_doc, output_path)` that exports the full stacked model as a single OBJ file with per-floor object groups (e.g., `g Floor_0_Walls`, `g Floor_1_Walls`).
- [ ] TASK-01-03: Add unit tests in `tests/test_blender_export_utils.py` for the pure helper logic (group name generation, path construction) — no FreeCAD dependency.
- [ ] TASK-01-04: Integrate the OBJ export call into `generate_floorplan.py` alongside existing DXF/STL exports, gated behind the `EXPORT_ARCHITECT_PACKAGE` env flag.
- [ ] TASK-01-05: Add an `OUT_OBJ` output directory constant and `ensure_output_dirs()` entry for `output/obj/`.

**Files / Surfaces**
- `src/blender_export_utils.py` — New file: OBJ export logic
- `src/generate_floorplan.py` — Add `export_floor_obj()` and `export_combined_obj()` calls
- `tests/test_blender_export_utils.py` — New file: pure helper tests
- `output/obj/` — New output directory

**Dependencies**
- None

**Exit Criteria**
- [ ] `python -m unittest discover -s tests -v` passes including new tests
- [ ] `python -m py_compile src/blender_export_utils.py` succeeds
- [ ] OBJ export produces `.obj` and `.mtl` files with named groups per floor
- [ ] Existing workflow (FCStd, DXF, SVG, STL) still works unchanged

**Phase Risks**
- **RISK-01-01:** FreeCAD's `Mesh.export()` may not support OBJ with named groups in all versions. Mitigation: test with STL fallback and document the OBJ group limitation; if OBJ groups fail, use object-name-based convention in the MTL file.

### PHASE-02 - Blender Scene Setup Script
**Goal**
Create a Python script that runs inside Blender headless mode, imports the combined OBJ, applies sensible default materials keyed by object group naming convention, adds architectural lighting and a camera, and saves a `.blend` file.

**Tasks**
- [ ] TASK-02-01: Create `src/setup_blender_scene.py` with a `main()` function that:
  1. Clears the default scene
  2. Imports the combined OBJ from `output/obj/tubehouse_full_3d.obj`
  3. Assigns materials by group name convention (walls → concrete gray, rooms → translucent fill, stairs → dark gray, slabs → medium gray)
  4. Adds a sun lamp (architectural, 45° elevation) and fill light
  5. Adds a camera targeted at the building center, framed for isometric or perspective view
  6. Saves to `output/blend/tubehouse_scene.blend`
- [ ] TASK-02-02: Create `src/blender_materials.py` with a material palette function that returns Blender material objects for the tubehouse (concrete, glass, steel, wood) using principled BSDF nodes.
- [ ] TASK-02-03: Add `material_assignments` to the floorplan spec or a sidecar config (`spec/blender_materials.json`) that maps room IDs/zone IDs to material names, so material assignment is data-driven rather than hardcoded.
- [ ] TASK-02-04: Add fallback import path: if Blender cannot find the OBJ, attempt STL import as a fallback.
- [ ] TASK-02-05: Ensure the script logs clear progress messages and gracefully handles missing Blender modules (so it can be syntax-checked without a Blender environment).

**Files / Surfaces**
- `src/setup_blender_scene.py` — New file: Blender scene assembly script
- `src/blender_materials.py` — New file: Material palette
- `spec/blender_materials.json` — New file: Material-to-room mapping config
- `output/blend/` — New output directory
- `src/blender_export_utils.py` — May need adjustments based on OBJ group naming

**Dependencies**
- PHASE-01 (OBJ export must produce importable files)

**Exit Criteria**
- [ ] `blender --background --python src/setup_blender_scene.py` completes without error
- [ ] Output `.blend` file opens in Blender with correct materials and lighting
- [ ] Script can be py_compile'd without Blender on PATH
- [ ] Material assignment matches the config in `spec/blender_materials.json`

**Phase Risks**
- **RISK-02-01:** Blender headless mode may not support EEVEE render on headless machines. Mitigation: Cycles CPU rendering is the default; EEVEE is opt-in.
- **RISK-02-02:** OBJ group naming from FreeCAD may not survive Blender's import pipeline intact. Mitigation: add a name-mapping table in `blender_materials.json` and a post-import rename pass in `setup_blender_scene.py`.

### PHASE-03 - Batch Runner Integration and Headless Render
**Goal**
Wire the Blender pipeline into `run.sh` (or a `run_blender.sh` companion) so that after FreeCAD generation, the OBJ export and Blender scene setup happen automatically, culminating in a headless Cycles render.

**Tasks**
- [ ] TASK-03-01: Add Blender availability check to `run.sh` (mirroring the FreeCAD/uv checks) or create a separate `run_blender.sh`.
- [ ] TASK-03-02: Add an `EXPORT_OBJ=1` and `BLENDER_RENDER=1` env flag section to the runner that:
  1. Runs FreeCAD generation with `EXPORT_ARCHITECT_PACKAGE=1` (triggers OBJ export)
  2. Runs `blender --background --python src/setup_blender_scene.py`
  3. Runs `blender --background --python src/render_blender.py` to produce a Cycles render
- [ ] TASK-03-03: Create `src/render_blender.py` — a minimal headless render script that opens the `.blend` file, renders Cycles at 1920×1080, and saves to `output/png/tubehouse_blender_render.png`.
- [ ] TASK-03-04: Update `AGENTS.md` with Blender pipeline entry points and the new env flags.
- [ ] TASK-03-05: Update `activeContext.md` with completed work and next-steps.

**Files / Surfaces**
- `run.sh` or `run_blender.sh` — Add Blender steps
- `src/render_blender.py` — New file: headless render script
- `AGENTS.md` — Document new entry points
- `activeContext.md` — Update with results

**Dependencies**
- PHASE-01 (OBJ export)
- PHASE-02 (Blender scene setup)

**Exit Criteria**
- [ ] `./run.sh` (or `./run_blender.sh`) produces OBJ + .blend + rendered PNG in one command
- [ ] Rendered PNG shows the tubehouse with default materials and lighting
- [ ] Failure at any stage produces a clear error message, not a silent failure
- [ ] FreeCAD-only workflow still works when Blender is not installed (graceful skip)

**Phase Risks**
- **RISK-03-01:** Blender headless render times may be long (5-10 min for Cycles on CPU). Mitigation: default to low sample count (64-128) with a note on increasing for final output.
- **RISK-03-02:** Different Blender versions may have API differences. Mitigation: target Blender 3.6 LTS and 4.x, add version check in the script.

## Verification Strategy
- **TEST-001:** `python -m unittest discover -s tests -v` — all pure-Python tests pass
- **TEST-002:** `python -m py_compile src/blender_export_utils.py src/setup_blender_scene.py src/blender_materials.py src/render_blender.py` — all scripts compile
- **MANUAL-001:** Run `EXPORT_OBJ=1 blender --background --python src/setup_blender_scene.py` and visually inspect the `.blend` file in Blender GUI — confirm materials, lighting, camera framing
- **MANUAL-002:** Run the full `run.sh` with Blender available and inspect `output/png/tubehouse_blender_render.png`
- **MANUAL-003:** Run `run.sh` without Blender installed — confirm it skips Blender steps gracefully and still produces FreeCAD artifacts

## Risks and Alternatives
- **RISK-001:** IfcOpenShell/BlenderBIM would provide richer BIM data exchange but adds a heavy dependency and steep learning curve. Phase-1 OBJ export keeps the path simple.
- **RISK-002:** Material assignment by group naming convention is fragile if FreeCAD changes object naming. The sidecar config (`spec/blender_materials.json`) mitigates this by making the mapping explicit and editable.
- **ALT-001:** Use FBX export instead of OBJ. FBX preserves more scene hierarchy but requires the FreeCAD `Import` module and has version-compatibility issues between FreeCAD and Blender. OBJ is simpler and more stable.
- **ALT-002:** Use BlenderBIM + IFC for full BIM interoperability. Deferred to a future phase because it requires IfcOpenShell installation and BIM property mapping, which adds significant scope.

## Grill Me
1. **Q-001:** Should the Blender pipeline be a separate `run_blender.sh` or integrated into the existing `run.sh`?
   - **Recommended default:** Separate `run_blender.sh` to keep FreeCAD-only workflow simple and avoid confusing errors when Blender is absent.
   - **Why this matters:** Integrated runner risks cluttering the FreeCAD-only path with Blender dependency checks.
   - **If answered differently:** If integrated, wrap Blender steps in conditional checks so `run.sh` works without Blender.

2. **Q-002:** What render engine should be the default for headless output?
   - **Recommended default:** Cycles CPU at 128 samples, 1920×1080 — portable, no GPU required.
   - **Why this matters:** EEVEE requires GPU/EGL context which is unavailable in most headless environments.
   - **If answered differently:** If you have a GPU server, EEVEE renders in seconds; Cycles takes minutes.

3. **Q-003:** Should the material palette be hardcoded in `blender_materials.py` or driven by the JSON sidecar?
   - **Recommended default:** JSON sidecar (`spec/blender_materials.json`) so non-developers can tweak materials without editing Python.
   - **Why this matters:** Architects and visualizers will want to iterate on material appearance rapidly.
   - **If answered differently:** Hardcoded palette is simpler but requires code changes for every material tweak.

4. **Q-004:** Should the Blender render script also produce an EEVEE preview render when a GPU is available?
   - **Recommended default:** No — keep the initial pipeline simple (Cycles only). Add EEVEE as a future enhancement.
   - **Why this matters:** EEVEE detection logic adds complexity to the render script.
   - **If answered differently:** If you need quick iteration feedback, EEVEE preview would be valuable.

5. **Q-005:** Do you want IFC export with IfcOpenShell as a phase-2 follow-up, or is OBJ sufficient for now?
   - **Recommended default:** OBJ for now; IFC/BlenderBIM as a future enhancement.
   - **Why this matters:** IFC adds IfcOpenShell as a dependency and requires BIM property mapping from the spec.
   - **If answered differently:** If you need BIM property round-tripping or structural analysis, IFC becomes important earlier.

## Suggested Next Step
Answer the Grill Me questions (especially Q-001, Q-002, Q-003), then begin PHASE-01 implementation by creating `src/blender_export_utils.py` and the OBJ export adapter.