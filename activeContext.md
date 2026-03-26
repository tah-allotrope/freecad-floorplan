# Active Context

## Project Info
- **Workspace:** `freecad-floorplan`
- **Objective:** Configure FreeCAD Model Context Protocol (MCP) to work with `opencode` for AI-assisted floorplan modeling.

## Current Task Plan
- [x] Create a minimal root `AGENTS.md` that follows the user's instruction-budget guidance.
- [x] Review `plans/home-design-to-architect-workflow.md` against the live repo state and identify stale or unimplemented items.
- [x] Implement the remaining repo changes needed to align the workflow with the current project state.
- [x] Verify the code paths that do not require a local FreeCAD binary and record any runtime blockers.
- [x] Update this file with final results and remaining follow-ups.

## Progress So Far
1. **MCP + repo setup:**
   - Installed `uv` to provide `uvx` for launching `freecad-mcp`.
   - Added local `opencode.json` config for the `freecad` MCP server via `uvx freecad-mcp`.
   - Previously verified `opencode mcp list` showed the MCP server as connected when the bridge and FreeCAD RPC listener were both running.
2. **Floor spec expansion:**
   - Extended `spec/floorplan-spec.json` with `F3` (Third Floor) and `F4` (Rooftop).
   - The spec now defines all 5 floors (`F0`-`F4`) for the 4m x 25m tubehouse.
3. **FreeCAD generation tooling:**
   - Added `stack_floors()` to `src/generate_floorplan.py` to build a combined 3D document (`tubehouse_full_3d.FCStd`).
   - Fixed stacked floor Z offsets to use cumulative per-floor heights from the spec instead of a single hard-coded storey height.
   - Fixed total building height reporting to use the same cumulative height logic.
   - Added shared pure helpers in `src/floorplan_utils.py` for floor height math.
4. **Runner + session helper fixes:**
   - Added `run.sh` as a one-command runner for FreeCAD generation.
   - Fixed `run.sh` so FreeCAD failures still print diagnostics and always clean up the background `freecad-mcp` process.
   - Added `src/freecad_session_starter.py` to summarize the project state and outputs.
   - Corrected the session helper to check the actual FreeCAD RPC listener (`localhost:9876` by default) rather than a nonexistent MCP TCP endpoint.
   - Converted the session helper output to ASCII-safe text so it runs cleanly in the default Windows terminal encoding.
5. **Tests + verification:**
   - Added `tests/test_floorplan_utils.py` to cover cumulative stacked offsets and total building height.
   - Verified successfully with:
     - `python -m unittest discover -s tests -v`
     - `bash -n run.sh`
     - `python src/freecad_session_starter.py`
6. **Documentation + planning notes:**
   - Added `plans/PROGRESS.md` and `plans/tubehouse-freecad-mcp-workflow.md` to capture the modeling workflow, project state, and recommended next steps.

## Outstanding / Next Session
1. **Generate the missing FreeCAD outputs:**
   - `output/fcstd/floorplan_F3.FCStd`
   - `output/dxf/floorplan_F3.dxf`
   - `output/svg/freecad_F3.svg`
   - `output/fcstd/floorplan_F4.FCStd`
   - `output/dxf/floorplan_F4.dxf`
   - `output/svg/freecad_F4.svg`
   - `output/fcstd/tubehouse_full_3d.FCStd`
   - `output/dxf/tubehouse_full_3d.dxf`
2. **Run inside FreeCAD to validate the full stack visually:**
   - In FreeCAD Python console: `exec(open(r'src/generate_floorplan.py').read())`
   - Then run: `stack_floors(spec['floors'])`
3. **Confirm runtime environment:**
   - FreeCAD RPC listener must be running (expected default `localhost:9876`).
   - `uvx freecad-mcp` must be running as the stdio bridge for opencode.
4. **Potential follow-up fixes after visual validation:**
   - Confirm combined DXF export from the stacked document behaves correctly in FreeCAD.
   - Check whether any F3/F4 room ids or labels should be normalized further after reviewing the rendered outputs.
5. **Suggested next modeling work once generation is confirmed:**
    - Add/adjust facade glazing and balcony railing details for `F3`/`F4`.
    - Consider BIM/IFC export or structural/MEP follow-up once the 3D massing is confirmed.

## Review / Results
- Added a minimal root `AGENTS.md` that keeps only repo-wide guidance and points deeper details to existing docs.
- Added `src/facade_utils.py` plus `tests/test_facade_utils.py` so facade/elevation logic is testable outside FreeCAD.
- Extended `src/generate_floorplan.py` to support the remaining workflow steps already described in the plan doc:
  - draws rooftop-only symbolic elements (`pergola`, `planter`, `solar_panels`)
  - draws a front facade elevation via `draw_front_facade(spec)`
  - exports optional architect-package artifacts via `export_architect_package(...)`
  - supports batch flags `GENERATE_STACKED=1`, `GENERATE_FACADE=1`, and `EXPORT_ARCHITECT_PACKAGE=1`
- Updated `run.sh` so the one-command path now attempts floors + stacked model + facade + package exports and reports PDFs / STL / PNG / manifest outputs.
- Updated `plans/home-design-to-architect-workflow.md` to match the actual repo state: F3/F4 are already specced, stacked/facade/package paths now exist in code, and remaining missing outputs depend on a local FreeCAD runtime.
- Corrected the stale RPC port note in `plans/PROGRESS.md` to `localhost:9876`.

## Verification
- Passed: `python -m unittest discover -s tests -v`
- Passed: `python -m py_compile src/generate_floorplan.py src/facade_utils.py src/freecad_session_starter.py src/floorplan_utils.py`
- Blocked locally: `freecadcmd --version` failed because `freecadcmd` is not installed / not on PATH in this environment.

## Remaining Follow-up
1. Install FreeCAD or expose `freecadcmd` on PATH, then run the batch workflow to generate F3/F4 outputs and the new facade/package artifacts.
2. If PDF export is required, ensure `cairosvg` is available in the FreeCAD Python environment used by `freecadcmd`.
3. If STL export is required, verify the FreeCAD `Mesh` module is available in the runtime.
