# AGENTS.md

## Scope
- This repo generates a 4 m x 25 m five-storey tube-house package from `spec/floorplan-spec.json` using FreeCAD Python scripts.
- Search the repo before assuming file locations beyond the high-level entry points below.

## Start Here
- Read `activeContext.md` for the current plan, blockers, and session results.
- Read `docs/lessons-learned.md` before changing FreeCAD automation.
- Use `plans/home-design-to-architect-workflow.md` for the end-to-end user workflow.

## Key Entry Points
- `spec/floorplan-spec.json` is the source of truth for floors, rooms, doors, and elements.
- `src/generate_floorplan.py` generates floor plans, the stacked massing model, the facade elevation, and export artifacts.
- `src/floorplan_utils.py` and `src/facade_utils.py` hold pure logic that should be tested outside FreeCAD.
- `src/blender_export_utils.py` exports OBJ/MTL from FreeCAD for Blender consumption.
- `src/blender_materials.py` defines the material palette and room/zone-to-material mappings.
- `src/setup_blender_scene.py` assembles a Blender scene (import OBJ, apply materials, add lights/camera).
- `src/render_blender.py` runs headless Cycles render from the assembled scene.
- `spec/blender_materials.json` is the data-driven material config sidecar (room/zone/obj group -> material assignments, lighting, camera, render).
- `run.sh` is the FreeCAD batch runner; `run_blender.sh` is the Blender visualization runner.

## Working Rules
- Prefer minimal, spec-driven changes; do not redesign floors unless the task explicitly asks for it.
- Keep the core zone and rear light well aligned across floors unless the user explicitly changes that rule.
- Put non-FreeCAD logic in pure helpers so it can be covered by `unittest`.
- Treat generated files in `output/` as reproducible artifacts; do not hand-edit them.

## Verification
- For pure Python changes, run `python -m unittest discover -s tests -v`.
- For script edits, also run `python -m py_compile src/*.py` when possible.
- If FreeCAD is unavailable locally, report that runtime limitation clearly instead of guessing.

## Progressive Docs
- Workflow/status details: `plans/PROGRESS.md`, `plans/tubehouse-freecad-mcp-workflow.md`
- Runtime/setup details: `freecad-mcp-guide.md`, `docs/HOW_TO_RUN.txt`
