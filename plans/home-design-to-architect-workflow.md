# Home Design to Architect Workflow
# FreeCAD + Claude MCP — End-to-End Plan

> **Purpose:** A plain-language roadmap so you can go from "I have an idea for my home" to "here is a floor plan package I can hand to an architect."
> **Your project so far:** A 4 m × 25 m Vietnamese tube house (nhà ống), 5 storeys. Floors 0–2 generated. Floors 3–4 and the full 3D massing model are outstanding.
> **Date:** 2026-03-26

---

## The Big Picture

```
STAGE 1          STAGE 2           STAGE 3          STAGE 4
You describe  →  Claude writes  →  FreeCAD draws  →  Export package
your ideas        the spec +         the plans          for architect
in plain text     Python code        in real CAD        (DXF / PDF / SVG)
```

You do not need to know FreeCAD. You do not need to know Python. You talk to Claude; Claude drives the software. Your only job is to describe what you want and review what gets produced.

---

## Part 1 — Where Things Stand Today

### What is already done

| Output | Status |
|---|---|
| Ground floor plan (F0) — garage / entry | Done — SVG + DXF + FCStd files exist |
| 1st floor plan (F1) — living room | Done |
| 2nd floor plan (F2) — bedrooms | Done |
| 3rd floor plan (F3) — home office / guest / master suite | Specced; generation pending a local FreeCAD run |
| 4th floor / rooftop plan (F4) | Specced; generation pending a local FreeCAD run |
| Full 3D massing model (all 5 floors stacked) | Code path exists; export pending a local FreeCAD run |
| Front facade elevation | Code path exists; export pending a local FreeCAD run |

The pipeline is working and proven. The remaining outputs are now blocked by runtime only: FreeCAD must be installed locally and available on PATH so the generator can run.

### What is already set up

- `freecad-floorplan/` project folder with all source files
- `spec/floorplan-spec.json` — the machine-readable description of your house
- `src/generate_floorplan.py` — the Python script that turns the spec into floor plans, the stacked 3D massing file, the facade elevation, and export artifacts
- `src/facade_utils.py` and `src/floorplan_utils.py` — pure helpers for geometry/layout calculations that are tested outside FreeCAD
- `run.sh` — one command that attempts floors + stacked massing + facade + export package generation
- `opencode.json` — MCP config so Claude/opencode can talk directly to FreeCAD
- `freecad-mcp-guide.md` — full setup instructions already written

---

## Part 2 — One-Time Setup (Do This Once)

If you have not already done this, work through these steps in order. Should take 30–45 minutes total.

### Step 1 — Install FreeCAD

Download and install FreeCAD 1.0 from freecad.org. Use all defaults.

After installing, add FreeCAD to your PATH so it can be called from the terminal:
- Search "environment variables" in the Windows Start Menu
- Edit the PATH variable
- Add: `C:\Program Files\FreeCAD 1.0\bin`

Test it worked:
```bash
freecad --version
# should print a version number
```

### Step 2 — Install the FreeCAD MCP Addon

This is the bridge that lets Claude talk to FreeCAD.

```bash
git clone https://github.com/neka-nat/freecad-mcp.git
# then copy the addon folder:
xcopy "freecad-mcp\addon\FreeCADMCP" "%APPDATA%\FreeCAD\Mod\FreeCADMCP" /E /I
```

Restart FreeCAD. In the Workbench dropdown, select **"MCP Addon"**. You should see a new toolbar with a **"Start RPC Server"** button.

### Step 3 — Install uv (tool runner)

```bash
pip install uv
```

### Step 4 — Verify the connection

Open FreeCAD, select MCP Addon workbench, click **Start RPC Server**.

Then in a terminal from this project folder:
```bash
cd C:\Users\tukum\Downloads\freecad-floorplan
opencode mcp list
```

You should see `freecad: connected`. If it says disconnected, FreeCAD is not running or the RPC server was not clicked.

---

## Part 3 — Your Design Workflow (Session by Session)

This is the repeating loop you use every time you work on your house design.

### Before each session (2 minutes)

1. Open FreeCAD
2. Select Workbench: **MCP Addon**
3. Click **Start RPC Server**
4. Open a terminal in `C:\Users\tukum\Downloads\freecad-floorplan`
5. Run `opencode` (or open Claude Desktop if you prefer the GUI)

### Starting each conversation with Claude

Paste this block at the start of every chat so Claude knows the project context:

```
We are working on a Vietnamese tube house floorplan project.
Folder: freecad-floorplan. Spec file: spec/floorplan-spec.json.
The building is 4000mm wide x 25000mm deep, 5 storeys (F0–F4).
1 unit = 1 mm. X = width (0=left), Y = depth (0=front/street), Z = height.
The core zone (lift + stairs + light well) sits at Y=15000–19000 on every floor — never move it.
Floors F0–F2 are done. F3 and F4 still need to be generated.
```

---

## Part 4 — How to Describe Your Ideas to Claude

You do not need to know CAD terminology. Just describe what you want in plain language. Claude will translate it into the spec and code.

### Useful conversation patterns

**To describe a room:**
> "On the 3rd floor I want the master bedroom to take up the full front of the house — maybe 4 metres wide and 6 metres deep, with a balcony at the front. The bathroom should be behind it, between the staircase and the rear light well."

**To ask for a layout suggestion:**
> "I have a 4m × 8m zone behind the core on the top floor. I want a rooftop kitchen and a covered terrace. What layout would work best for a tropical climate?"

**To request a change:**
> "Move the bathroom door from the north wall to the east wall. The opening should be 900mm wide."

**To check what has been drawn:**
> "Show me the current state of F3 — what rooms are in the spec and what has been generated?"

**To see a visual:**
> "Take a screenshot of the current FreeCAD view so I can see what F3 looks like."

Claude will handle all of the spec editing, Python scripting, and FreeCAD commands. You just review and give feedback.

---

## Part 5 — Immediate Next Steps (Prioritised)

Work through these in order. Each one builds on the previous.

### STEP A — Complete the floor plans for F3 and F4

**Why first:** The architect needs all 5 floors. The pipeline is already proven for F0–F2.

**What to do — in Claude:**
1. Open a session with the context block from Part 3.
2. Say: *"Read the current floorplan-spec.json and show me what F3 and F4 are supposed to contain based on the design notes."*
3. Review the existing F3/F4 spec entries and adjust them if you want layout changes before generation.
4. Run the generator in FreeCAD: `freecadcmd src/generate_floorplan.py`
5. If you want only the top floors regenerated interactively, open FreeCAD and run `draw_floor(spec, spec['floors'][3])` and `draw_floor(spec, spec['floors'][4])`.
6. After generation, open the SVG or FCStd outputs and review screenshots / plans.

**Expected output files after this step:**
- `output/fcstd/floorplan_F3.FCStd`
- `output/dxf/floorplan_F3.dxf`
- `output/svg/freecad_F3.svg`
- Same set for F4

---

### STEP B — Generate the full 3D massing model

**Why:** A single 3D view of all 5 floors stacked is the most convincing thing to show an architect at an early stage. It communicates the building volume and proportions instantly.

**What to do — in Claude:**
> "Create the full 3D massing model and save it to `output/fcstd/tubehouse_full_3d.FCStd`. Then export a DXF and capture an isometric screenshot if the FreeCAD GUI is available."

The `stack_floors()` function is already written in `src/generate_floorplan.py`. In FreeCAD, run `stack_floors(spec['floors'])`. In batch mode, set `GENERATE_STACKED=1` before launching the script.

**Expected output:** `output/fcstd/tubehouse_full_3d.FCStd`, `output/dxf/tubehouse_full_3d.dxf`, and `output/png/tubehouse_full_3d_isometric.png` when GUI screenshots are available.

---

### STEP C — Review and refine the plans

With all 5 floors generated, go through each one visually:

1. Open each SVG in a browser: open `output/svg/freecad_F0.svg` etc.
2. Note anything you want to change (room sizes, door positions, window locations).
3. Give Claude the changes in plain language, floor by floor.
4. Regenerate each floor after changes.

Typical things to refine at this stage:
- Balcony sizes and positions
- Bathroom layouts
- Door swing directions
- Kitchen / dining zone configuration
- Staircase landing widths

---

### STEP D — Add facade detail

**Why:** The street-facing facade (4m wide, 5 storeys) is what makes this a tube house. It communicates the design intent to the architect most clearly.

**What to do — in Claude:**
> "Draw the front facade elevation. Show all 5 floors. Each floor should show the window/balcony opening. Floor 1 has a full-width balcony with a railing. Floors 2 and 3 have smaller balconies. Floor 4 is a setback terrace."

This is now automated by `draw_front_facade(spec)` in `src/generate_floorplan.py`, which writes `output/fcstd/front_facade_elevation.FCStd`, `output/dxf/front_facade_elevation.dxf`, and `output/svg/front_facade_elevation.svg`.

---

### STEP E — Export the architect package

Once the plans and facade are in good shape, export everything into formats an architect can use.

**What to ask Claude:**
> "Export the architect package: floor PDFs, facade PDF, stacked-model STL, and the package manifest."

**Standard architect formats this pipeline can produce:**

| Format | What it is | How to use it |
|---|---|---|
| `.dxf` | Industry-standard 2D CAD drawing | Opens in AutoCAD, Revit, SketchUp, any CAD tool |
| `.svg` | Scalable vector — perfect for printing or sharing | Open in browser, print to PDF, or attach to email |
| `.FCStd` | FreeCAD native file | Share if the architect uses FreeCAD |
| `.stl` | 3D mesh — for 3D printing a massing model | Exported from the stacked document when Mesh export is available |
| `.pdf` | Print-ready | Generated from SVG when `cairosvg` is available in the FreeCAD Python environment |

**Recommended handoff package for an architect:**
- One PDF per floor (5 floor plans + 1 facade elevation = 6 PDFs)
- One DXF per floor plus `front_facade_elevation.dxf`
- One isometric screenshot / rendered view of the 3D massing model as PNG
- `output/architect_package_manifest.json` so you can see which exports succeeded and which optional exports were skipped

---

### STEP F (Optional, after architect feedback) — BIM/IFC upgrade

If the architect uses BIM software (Revit, ArchiCAD), they may ask for an IFC file. IFC is the open standard for building models with semantic data (walls know they are walls, doors know they are doors).

FreeCAD's BIM Workbench can export IFC. This requires redrawing the walls using `Arch.makeWall()` instead of the current `Draft.makeWire()` approach — a moderate effort but completely doable via Claude + MCP.

Hold off on this until the architect asks for it. Most early-stage conversations work fine with DXF + PDF.

---

## Part 6 — Quick Reference: Session Startup Commands

```bash
# Terminal 1 — start in the project folder
cd C:\Users\tukum\Downloads\freecad-floorplan

# Check FreeCAD is on PATH
freecad --version

# Verify MCP connection (FreeCAD must already be open with RPC server running)
opencode mcp list

# Start opencode session
opencode
```

```bash
# To run the full batch workflow (floors + stacked model + facade + package exports):
GENERATE_STACKED=1 GENERATE_FACADE=1 EXPORT_ARCHITECT_PACKAGE=1 freecadcmd src\generate_floorplan.py
# This still needs FreeCAD installed locally; PNG screenshots require the GUI module to be available
```

```bash
# To preview SVG floor plans in browser:
cd output/svg
python -m http.server 8765
# then open http://localhost:8765 in browser
```

---

## Summary Checklist

- [ ] **Setup:** FreeCAD installed, MCP addon installed, `opencode mcp list` shows `freecad: connected`
- [ ] **F3 floor plan:** rooms already in spec; FCStd + DXF + SVG generated locally
- [ ] **F4 floor plan:** rooftop layout already in spec; FCStd + DXF + SVG generated locally
- [ ] **3D massing model:** all 5 floors stacked in `tubehouse_full_3d.FCStd`, DXF exported, isometric screenshot taken when GUI is available
- [ ] **Plan review:** all 5 floors reviewed visually, changes requested and applied
- [ ] **Facade elevation:** front elevation drawn and exported
- [ ] **Architect package exported:** floor PDFs, facade PDF, DXFs, STL if available, and a massing screenshot
- [ ] **(Optional) IFC export:** only if architect requests BIM format
