---
title: "Blender Install and Integration Demo"
date: "2026-05-09"
status: "draft"
request: "Install Blender, generate tube-house OBJ output from existing FreeCAD model, run Blender scene assembly and render"
plan_type: "multi-phase"
research_inputs:
  - "research/2026-04-30_adding-blender-freecad-workflow.md"
---

# Plan: Blender Install and Integration Demo

## Objective
Install Blender on the local machine, use FreeCAD (via MCP) to generate OBJ exports from the existing 4×25m tubehouse model, then run the Blender scene assembly and Cycles render pipeline end-to-end, producing a visual demonstration that the full integration works.

## Context Snapshot
- **Current state:** Three phases of Blender integration code are committed and tested (35 pure-Python tests pass). FreeCAD MCP is connected. OBJ export code exists in `src/blender_export_utils.py` but has never been executed. No `output/obj/`, `output/stl/`, `output/blend/`, or `output/png/` directories exist. Blender is not installed locally. Existing FreeCAD artifacts exist for F0-F2 (FCStd, DXF, SVG) but F3 and F4 are missing.
- **Desired state:** Blender installed and on PATH; OBJ exports generated for all 5 floors and the combined model; Blender scene assembled with materials, lighting, and camera; Cycles render produced as PNG; all output artifacts verified.
- **Key repo surfaces:**
  - `src/generate_floorplan.py` — main generation script (OBJ export wired in)
  - `src/blender_export_utils.py` — OBJ/MTL export functions
  - `src/blender_materials.py` — material palette and Blender material creation
  - `src/setup_blender_scene.py` — scene assembly script
  - `src/render_blender.py` — headless Cycles render
  - `spec/blender_materials.json` — data-driven config
  - `run.sh` — FreeCAD batch runner
  - `run_blender.sh` — Blender batch runner
  - FreeCAD MCP server — available via `freecad-mcp` for headless FreeCAD execution
- **Out of scope:**
  - Changes to the floorplan spec or existing generation code
  - IFC/BlenderBIM integration
  - Material palette tuning (will use defaults)
  - EEVEE render mode

## Research Inputs
- `research/2026-04-30_adding-blender-freecad-workflow.md` — Recommends OBJ as interchange format, confirms FreeCAD for parametric modeling and Blender for downstream rendering.

## Assumptions and Constraints
- **ASM-001:** Blender 4.x portable or installed binary can be obtained and placed on PATH or referenced via `BLENDER_CMD` env var.
- **ASM-002:** The FreeCAD MCP server is running and the FreeCAD RPC listener is accessible, allowing headless execution of `generate_floorplan.py` to produce OBJ files.
- **ASM-003:** The existing `output/fcstd/` files for F0-F2 confirm FreeCAD can generate geometry; F3 and F4 outputs are missing but the spec includes them.
- **CON-001:** Cycles CPU rendering at 128 samples × 1920×1080 may take 5-10 minutes on typical hardware. This is acceptable for a demo.
- **DEC-001:** Blender will be installed via the official Windows installer to `C:\Program Files\Blender Foundation\Blender 4.1\` or equivalent, and the `BLENDER_CMD` env var will be set if not on PATH.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Install Blender and verify CLI access | None | `blender --version` succeeds |
| PHASE-02 | Generate OBJ exports from FreeCAD via MCP | PHASE-01 (Blender install) | `output/obj/tubehouse_full_3d.obj`, per-floor OBJ files |
| PHASE-03 | Run Blender scene assembly and Cycles render | PHASE-02 | `output/blend/tubehouse_scene.blend`, `output/png/tubehouse_blender_render.png` |

## Detailed Phases

### PHASE-01 - Install Blender and Verify
**Goal**
Download and install Blender 4.x on Windows, verify the CLI is accessible.

**Tasks**
- [ ] TASK-01-01: Download Blender 4.1 LTS from https://www.blender.org/download/ (MSI installer for Windows).
- [ ] TASK-01-02: Install Blender to the default location (`C:\Program Files\Blender Foundation\Blender 4.1\`).
- [ ] TASK-01-03: Verify `blender --version` works from a terminal, or set `BLENDER_CMD` env var to the full path.
- [ ] TASK-01-04: Run `blender --background --python -c "import bpy; print(bpy.app.version_string)"` to confirm the Python API is functional.

**Files / Surfaces**
- Blender installation at `C:\Program Files\Blender Foundation\Blender 4.1\blender.exe`
- `run_blender.sh` lines 46-68 (candidate search paths)

**Dependencies**
- None

**Exit Criteria**
- [ ] `blender --version` prints a 4.x version number
- [ ] `blender --background --python -c "import bpy; print('OK')"` exits with code 0

**Phase Risks**
- **RISK-01-01:** Blender installer may require admin privileges. Mitigation: run installer as administrator.
- **RISK-01-02:** Windows Defender or antivirus may block the download. Mitigation: whitelist the Blender installer URL.

### PHASE-02 - Generate OBJ Exports from FreeCAD
**Goal**
Use the FreeCAD MCP server to generate OBJ exports for all floors and the combined stacked model.

**Tasks**
- [ ] TASK-02-01: Ensure the FreeCAD MCP server and FreeCAD RPC listener are running (`uvx freecad-mcp` + FreeCAD GUI open, or `freecadcmd` available).
- [ ] TASK-02-02: Execute the generation pipeline via MCP to produce OBJ files: run `generate_floorplan.py` with `GENERATE_STACKED=1 GENERATE_FACADE=1 EXPORT_ARCHITECT_PACKAGE=1` env flags, which triggers `export_floor_obj()` per floor and `export_combined_obj()` for the stacked model.
- [ ] TASK-02-03: Verify `output/obj/` contains `floorplan_F0.obj` through `floorplan_F4.obj` and `tubehouse_full_3d.obj` plus `tubehouse.mtl`.
- [ ] TASK-02-04: Spot-check one OBJ file for named groups (e.g., `g F0_Wall_ext_left_2D`) and one MTL file for material references.

**Files / Surfaces**
- `src/generate_floorplan.py` — entry point (env flags trigger OBJ export)
- `src/blender_export_utils.py` — `export_floor_obj()`, `export_combined_obj()`, `write_mtl()`
- `output/obj/` — target directory for OBJ/MTL files

**Dependencies**
- PHASE-01 (Blender must be installed to verify end-to-end; OBJ generation only needs FreeCAD)

**Exit Criteria**
- [ ] `output/obj/tubehouse_full_3d.obj` exists and is > 0 bytes
- [ ] `output/obj/tubehouse.mtl` exists and contains `newmtl Concrete_Wall` and `newmtl Glass_Glazing`
- [ ] At least one per-floor OBJ file (e.g., `output/obj/floorplan_F0.obj`) contains `g ` group lines
- [ ] No errors in the FreeCAD generation output

**Phase Risks**
- **RISK-02-01:** The FreeCAD `Mesh` module may not be available in the headless `freecadcmd` path, causing OBJ export to fail while other exports succeed. Mitigation: if OBJ fails, fall back to STL (`output/stl/`) which already exists as an export path in the code.
- **RISK-02-02:** F3/F4 floor specs may have geometry that fails during generation. Mitigation: the spec already includes F3/F4; any failure will be visible in the FreeCAD output logs.

### PHASE-03 - Blender Scene Assembly and Render
**Goal**
Run `setup_blender_scene.py` to import the combined OBJ, apply materials, add lighting and camera, save the `.blend` file, then run `render_blender.py` to produce a Cycles render.

**Tasks**
- [ ] TASK-03-01: Run `blender --background --python src/setup_blender_scene.py` and verify no errors. Confirm `output/blend/tubehouse_scene.blend` is created.
- [ ] TASK-03-02: Open `output/blend/tubehouse_scene.blend` in Blender GUI (optional but recommended for visual verification).
- [ ] TASK-03-03: Run `blender --background output/blend/tubehouse_scene.blend --python src/render_blender.py` to produce the Cycles render.
- [ ] TASK-03-04: Verify `output/png/tubehouse_blender_render.png` exists and is a non-trivial image (> 10 KB).
- [ ] TASK-03-05: Take a screenshot of the render for documentation.

**Files / Surfaces**
- `src/setup_blender_scene.py` — scene assembly
- `src/render_blender.py` — Cycles render
- `spec/blender_materials.json` — material/lighting/camera config
- `output/blend/tubehouse_scene.blend` — output scene
- `output/png/tubehouse_blender_render.png` — output render

**Dependencies**
- PHASE-01 (Blender must be installed)
- PHASE-02 (OBJ files must exist)

**Exit Criteria**
- [ ] `output/blend/tubehouse_scene.blend` exists and is > 100 KB
- [ ] `output/png/tubehouse_blender_render.png` exists and is > 10 KB
- [ ] Opening the `.blend` file in Blender shows the tubehouse mesh with default materials applied
- [ ] The render PNG shows a visible building (not a blank/transparent image)

**Phase Risks**
- **RISK-03-01:** Cycles CPU render at 128 samples may take 5-10 minutes. Mitigation: the render script is configurable; lower sample counts can be set via `BLENDER_RENDER_SAMPLES` env var for faster demos.
- **RISK-03-02:** Blender may fail to import the OBJ if FreeCAD's `Mesh.export()` produced non-standard geometry. Mitigation: the setup script has an STL fallback path; if OBJ fails, check `output/stl/` and rerun with `TUBEHOUSE_STL` env var.
- **RISK-03-03:** The camera may not frame the building well on first run. Mitigation: camera position is configurable in `spec/blender_materials.json` under the `camera` key.

## Verification Strategy
- **MANUAL-001:** Visual inspection of `output/png/tubehouse_blender_render.png` — building should be visible with recognizable geometry and lighting.
- **MANUAL-002:** Open `output/blend/tubehouse_scene.blend` in Blender GUI — confirm Sun_Light, Fill_Light, and Tubehouse_Camera objects exist in the outliner.
- **MANUAL-003:** Check Blender console output during setup and render for errors or warnings about missing materials or geometry.
- **OBS-001:** Compare the render PNG file size to ensure it's a valid image (> 10 KB typically indicates content).

## Risks and Alternatives
- **RISK-001:** If Blender cannot be installed (e.g., admin restrictions), the OBJ/MTL files can still be imported into Blender on a different machine using the same scripts, since the pipeline is fully scripted.
- **ALT-001:** If the FreeCAD MCP path fails, the user can run FreeCAD GUI directly and execute `generate_floorplan.py` from the Python console.
- **ALT-002:** If Cycles render is too slow, reduce to 32 samples via `BLENDER_RENDER_SAMPLES=32 blender --background ...` for a faster preview.

## Grill Me
No open clarification questions. The plan is self-contained: install Blender, run the existing pipeline, verify output.

## Suggested Next Step
Install Blender (TASK-01-01), then proceed to generate FreeCAD OBJ exports via MCP (TASK-02-02), then assemble and render the Blender scene (TASK-03-01 through TASK-03-04).