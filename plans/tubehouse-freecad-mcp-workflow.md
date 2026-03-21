# Tubehouse FreeCAD + MCP Workflow Plan
### 4 m × 25 m — 5 storeys — Vietnamese nhà ống
*Written for a complete FreeCAD beginner using Claude / opencode as the AI driver*

---

## Quick Overview

This repo already has a working pipeline:

```
JSON spec  →  Python script  →  FreeCAD  →  FCStd + DXF + SVG
```

The **MCP server** adds a second, interactive layer on top:

```
You (natural language)  →  Claude/opencode  →  MCP  →  FreeCAD (live)
```

Both modes work together. The script approach is best for **batch regeneration**; the MCP approach is best for **exploration and one-off tweaks** when you want to talk to FreeCAD conversationally.

**Current status:** Floors 0–2 (Ground + 2 upper) are done. Floors 3 and 4 still need to be added. The full 3D massing (stacking floors into one building) has not been done yet.

---

## Part 1 — How the FreeCAD MCP Server Works

### The architecture

```
┌─────────────────────────────┐
│  AI client (opencode/Claude)│
│  reads MCP tools, sends     │
│  execute_code calls         │
└──────────────┬──────────────┘
               │ stdio (uvx freecad-mcp)
┌──────────────▼──────────────┐
│  freecad-mcp MCP server     │
│  (Python process, uvx)      │
│  translates MCP ↔ XML-RPC   │
└──────────────┬──────────────┘
               │ XML-RPC (localhost:9876 default)
┌──────────────▼──────────────┐
│  FreeCAD (running on screen)│
│  MCP Addon = RPC listener   │
│  executes Python in-process │
└─────────────────────────────┘
```

FreeCAD must be **running and visible** with the RPC server started. The AI does not launch FreeCAD itself — you have to open it and click "Start RPC Server" each time.

### MCP tools available

| Tool | What it does | Power level |
|------|-------------|-------------|
| `execute_code` | Run any Python string inside FreeCAD | ⭐⭐⭐⭐⭐ |
| `get_objects` | List all objects in the active document | ⭐⭐⭐ |
| `get_object` | Read one object's properties | ⭐⭐⭐ |
| `create_document` | Open a new document | ⭐⭐ |
| `create_object` | Create a simple object by type | ⭐⭐ |
| `edit_object` | Set a property on an existing object | ⭐⭐ |
| `delete_object` | Remove an object | ⭐⭐ |
| `get_view` | Capture a screenshot of the 3D view | ⭐⭐⭐ |
| `insert_part_from_library` | Insert a standard Part library shape | ⭐ |

**The killer tool is `execute_code`.** It lets Claude write and run arbitrary FreeCAD Python — which means anything the FreeCAD API can do, Claude can do. All the heavy lifting in this project (`make_box`, `Draft.makeWire`, DXF export, etc.) goes through `execute_code`.

### What "text-only feedback" means

By default, `get_view` returns a screenshot PNG so the AI can see what it drew. This uses tokens. Pass `--only-text-feedback` in `opencode.json` to skip screenshots and save tokens — useful once you've confirmed the model works and just want fast iteration.

---

## Part 2 — Setup: Step-by-Step for a Complete Beginner

### Step 1 — Install FreeCAD

Download the latest stable release (0.21 or 1.0) from https://www.freecad.org/downloads.php

Install with all defaults. On Windows, the installer adds FreeCAD to the Start Menu but **not** to PATH by default. To fix this, add `C:\Program Files\FreeCAD 0.21\bin` to your system PATH (search "environment variables" in the Start Menu).

Test it works: open a terminal and type `freecad --version`. You should see a version number.

### Step 2 — Install the FreeCAD MCP addon

1. Clone the freecad-mcp repository somewhere on your computer:
   ```bash
   git clone https://github.com/neka-nat/freecad-mcp.git
   ```
2. Copy the `addon/FreeCADMCP` folder to your FreeCAD Mod directory:
   - **Windows:** `C:\Users\YOUR_NAME\AppData\Roaming\FreeCAD\Mod\`
   - **Mac:** `~/Library/Application Support/FreeCAD/Mod/`
   - **Linux:** `~/.FreeCAD/Mod/`
3. Restart FreeCAD.
4. In FreeCAD, open the Workbench dropdown (top toolbar, shows "Start" by default) and select **"MCP Addon"**.
5. A toolbar appears. Click **"Start RPC Server"**. A message in the FreeCAD status bar should confirm it's running.

### Step 3 — Install uv (Python tool runner)

```bash
pip install uv
```

This gives you the `uvx` command, which the `opencode.json` config uses to launch the MCP server bridge automatically.

### Step 4 — Install opencode

```bash
npm install -g @opencode-ai/opencode
```

Or follow the install instructions at https://opencode.ai — opencode is the terminal AI client used here (like Claude in a terminal, but MCP-aware and model-agnostic).

### Step 5 — Configure your LLM

Run `opencode` once to go through the setup wizard. You can choose:
- **Anthropic (Claude)** — paste your API key from console.anthropic.com
- **Google (Gemini)** — paste your API key from aistudio.google.com
- **OpenAI, Mistral, local Ollama** — also supported

Claude Sonnet 4.x is recommended for code generation quality. Gemini 2.5 Pro is a strong alternative with a very large context window (useful when you want to paste the entire spec + script in one shot).

### Step 6 — Verify the connection

With FreeCAD running and the RPC server started:

```bash
cd freecad-floorplan
opencode mcp list
```

You should see `freecad` with status `connected`. If it shows `disconnected`, check that you clicked "Start RPC Server" in FreeCAD and that FreeCAD is still open.

### Step 7 — Start a conversation

```bash
opencode
```

Type a prompt like: *"List all objects in the current FreeCAD document"* — it will call `get_objects` and show you what's there.

---

## Part 3 — Tubehouse Modelling Strategy

### Design specs recap

| Parameter | Value |
|-----------|-------|
| Footprint | 4 m × 25 m |
| Plot width | 4,000 mm |
| Plot depth | 25,000 mm |
| Storeys | 5 (Ground floor = F0, F1–F4 upper floors) |
| Floor-to-ceiling | 3,500 mm (adjust per floor if needed) |
| Total building height | ~18,500 mm (5 × 3,500 mm + slab thicknesses) |
| Style | Vietnamese nhà ống (tube house) |
| Climate | Tropical — cross-ventilation and light wells are structural requirements, not aesthetics |

### Core spatial rules for this tube house

Every floor shares the same **core zone** at Y = 15,000–19,000 mm:
- Lift shaft: X = 200–1,000 (800 mm wide)
- Staircase: X = 1,100–2,700 (1,600 mm wide)
- Internal light well: X = 2,800–3,800 (1,000 mm wide)

The **rear light well** at Y = 23,000–25,000 mm also repeats on every floor.

These two elements must never change between floors. Only the front zone (Y = 0–15,000) and the behind-core zone (Y = 19,000–23,000) change.

### Floor plan for all 5 floors

| Floor | Level | Front zone (Y 0–15,000) | Behind-core (Y 19,000–23,000) |
|-------|-------|------------------------|-------------------------------|
| Ground | F0 | Garage / commercial / entry | Utility / WC |
| 1st upper | F1 | Living room + front balcony | Kitchen + bathroom |
| 2nd upper | F2 | 3 bedrooms | Ensuite + laundry |
| 3rd upper | F3 | Master suite + study | Master bathroom |
| 4th upper (top) | F4 | Rooftop terrace + plant room | Sky kitchen / rooftop bar |

Floors F0–F2 are already in `spec/floorplan-spec.json`. F3 and F4 need to be added following the same JSON schema.

### Recommended modelling workflow order

**Phase 1 — 2D floor plans (do this first)**

1. Design each floor as an SVG sketch first (visual iteration is fast)
2. Review SVG in browser: `cd output/svg && python -m http.server 8765`, open `http://localhost:8765/floor_N_preview.svg`
3. Translate approved layout into `spec/floorplan-spec.json` (add to the `"floors"` array)
4. Run `generate_floorplan.py` inside FreeCAD → get FCStd + DXF + SVG per floor
5. Repeat for each floor

**Phase 2 — 3D massing model (do after all 5 floors are done)**

The current script creates 3D walls and slabs but each floor is a **separate document**. To get a full 5-storey building in one view:

1. Create a new FreeCAD document: `Tubehouse_3D_Massing.FCStd`
2. Use `execute_code` via MCP to stack all floor slabs and walls at their correct Z heights:
   - F0: Z = 0 to 3,500 mm
   - F1: Z = 3,500 to 7,000 mm
   - F2: Z = 7,000 to 10,500 mm
   - F3: Z = 10,500 to 14,000 mm
   - F4: Z = 14,000 to 17,500 mm
3. Apply basic materials/colours per floor
4. Export to STL for 3D printing or PDF for presentation

**Phase 3 — Architecture workbench (advanced, optional)**

FreeCAD's **Arch workbench** (now called BIM workbench in FreeCAD 1.0) has wall, window, door, floor, and building objects that carry semantic data (IFC-compatible). This is the "proper" architectural workflow:
- `Arch.makeWall()` creates walls from sketch profiles
- `Arch.makeWindow()` creates windows with proper jamb reveals
- `Arch.makeFloor()` creates floor levels
- `Arch.makeBuilding()` groups everything into an IFC Building object

The current approach (Draft.makeWire rectangles) is simpler and works fine for 2D drawings and massing. Switch to Arch workbench only if you need IFC export or want to do thermal/structural analysis.

**Phase 4 — Facade detail (advanced)**

For the street-facing facade (Y = 0):
- Typical Vietnamese tube house facade: 3–4 m wide, full-height louvred shutters or folding aluminium windows on each floor
- The facade changes per floor (balcony railing on F1–F3, setback terrace on F4)
- Model this with Part::Box shapes for window frames + openings in the front wall

---

## Part 4 — LLM Prompting Strategy

### Golden rule

Claude and Gemini both work best with FreeCAD when you:
1. Give them the **exact coordinate system** upfront (1 unit = 1 mm, X = width, Y = depth, Z = height)
2. Ask for **one specific thing** per prompt — not "build the whole floor"
3. Always ask them to use **`execute_code`** rather than `create_object` — it's more powerful and predictable
4. Tell them to **`doc.recompute()` before saving** — FreeCAD won't show changes without this

### Starter context block (paste this at the start of every session)

```
We are working in FreeCAD on a Vietnamese tube house.
Coordinate system: 1 unit = 1 mm. X = plot width (0=left, 4000=right).
Y = plot depth (0=front/street, 25000=rear). Z = height above floor (0=floor level).
All operations go through execute_code. Always end scripts with doc.recompute().
The active document is named Tubehouse_F{N} where N is the floor level.
```

### Example prompts for key operations

---

**Creating a new FreeCAD document and basic setup:**
```
Open a new FreeCAD document called "Tubehouse_F3". Set up layer groups:
2D_PLAN containing WALLS, ROOMS, SYMBOLS, LABELS, DIMENSIONS.
3D_MODEL for extruded objects. Use execute_code.
```

---

**Drawing the exterior walls of a floor:**
```
In the active FreeCAD document, draw the four exterior walls of the tube house
using Draft.makeWire rectangles. The plot is 4000mm wide × 25000mm deep.
All exterior walls are 200mm thick. So:
- Left wall: x=0, y=0, w=200, h=25000
- Right wall: x=3800, y=0, w=200, h=25000
- Front wall: x=0, y=0, w=4000, h=200
- Rear wall: x=0, y=24800, w=4000, h=200
Add them to the WALLS group. ShapeColor = (0.20, 0.25, 0.33). Use execute_code.
```

---

**Drawing a floor slab in 3D:**
```
In the 3D_MODEL group, create a floor slab for F3 using Part::Box.
Position: x=0, y=0, z=-200. Size: Length=4000, Width=25000, Height=200.
Label it "Floor_Slab_3D". ShapeColor = (0.75, 0.75, 0.75). Use execute_code.
```

---

**Drawing the core zone (repeat this for every floor):**
```
Draw the core zone walls for this floor. The core sits at Y=15000-19000.
Interior walls (100mm thick):
- Lift/stair separator: x=1000, y=15000, w=100, h=4000
- Stair/lightwell separator: x=2700, y=15000, w=100, h=4000
- Core front wall: x=200, y=15000, w=3600, h=100  (with door opening x=1100-1900)
- Core rear wall: x=200, y=19000, w=3600, h=100   (with door opening x=1100-1900)
Draw these as 3 solid rectangles (skip the door openings for now) plus
the horizontal partition wall between core and rear zone.
Add to WALLS group. Use execute_code.
```

---

**Adding a room fill (coloured rectangle):**
```
Add a filled rectangle for the living room on this floor.
Room bounds: x=200, y=2100, w=3600, h=12800. Label: "Living_Room".
Add to ROOMS group. ShapeColor = (0.98, 1.00, 0.96). Transparency = 30.
Use execute_code with Draft.makeWire, closed=True, face=True.
```

---

**Adding a door (swing type):**
```
Add a swing door at the core-to-living transition wall.
The opening is at x=1100-1900, y=15000 (wall thickness 100mm).
Leaf: line from (1100, 15000) to (1100, 14100) — 900mm long, swings into living room.
Arc: centre (1100, 15000), radius 900, from 270° to 360°.
Add leaf and arc to SYMBOLS group. Use execute_code with Draft.makeLine and Draft.makeCircle.
```

---

**Stacking floors for the 3D massing model:**
```
Create a new document "Tubehouse_3D_Massing". For each floor 0–4, create a
simple extruded box representing the floor plate:
- x=0, y=0, z = floor_level * 3700
- Length=4000, Width=25000, Height=3500
- Label: "Floor_F{N}_Mass"
- Color: alternate between (0.9, 0.9, 0.85) and (0.85, 0.88, 0.92)
Add all boxes, then doc.recompute(). Use execute_code.
```

---

**Getting a screenshot to check progress:**
```
Take a screenshot of the current FreeCAD view using get_view.
Then set the view to isometric: use execute_code to call
FreeCADGui.activeDocument().activeView().viewIsometric()
then take another screenshot.
```

---

**Exporting to DXF:**
```
Export all objects in the WALLS, STAIRS, SYMBOLS, LABELS, and DIMENSIONS groups
to a DXF file at output/dxf/floorplan_F3.dxf.
Use execute_code with import importDXF; importDXF.export([...], path).
Collect objects using grp.OutList for each group.
```

---

**Debugging when nothing appears in the view:**
```
The FreeCAD document seems empty or objects are not visible. Please:
1. Call doc.recompute()
2. Call FreeCADGui.activeDocument().activeView().fitAll()
3. Use get_objects to list what's in the document
4. If objects exist but are invisible, loop through all objects and set
   obj.ViewObject.Visibility = True
Use execute_code.
```

---

### Prompt patterns that work well

**"Write a reusable function, then call it"** — Instead of one giant script, ask Claude to write a helper function like `def draw_core_zone(doc, grp_walls, floor_z):` and call it. This is easier to debug and reuse.

**"Show me the current state first"** — Before making changes, ask Claude to call `get_objects` and describe what it sees. This prevents duplicate objects.

**"Translate this JSON spec entry into FreeCAD calls"** — Paste a single floor entry from `floorplan-spec.json` and ask Claude to write the `execute_code` script for it. This is exactly how `generate_floorplan.py` was built.

**"What went wrong?"** — If you get a Python error from FreeCAD, paste the error into the chat and ask Claude to fix it. Claude is good at debugging FreeCAD API mismatches.

---

## Part 5 — Gaps and Workarounds

### Gap 1: No persistent variables between `execute_code` calls

Each `execute_code` call is independent — you can't define a variable in one call and reference it in the next.

**Workaround:** Either do everything in one large `execute_code` call, or use FreeCAD's document object itself as shared state: `doc = FreeCAD.activeDocument()` at the top of each call to re-acquire the document handle.

### Gap 2: No visual selection via MCP

You can't "click" to select objects through MCP. Selection-dependent operations (like FreeCAD's Fillet or Chamfer which require edge selection) can't be driven by MCP alone.

**Workaround:** Use coordinate-based Python API calls instead. `Part.makeBox()` doesn't need selection. For operations that truly require selection (e.g., Boolean subtraction of two specific shapes), use `doc.getObject("shape_name")` to get handles by label.

### Gap 3: PartDesign Sketcher requires interactive mode

FreeCAD's PartDesign → Sketch workflow (the "parametric modelling" approach) is GUI-first. While sketches can be created via Python API, it's verbose and error-prone.

**Workaround:** Use the **Draft workbench** approach (as this project does) — create geometry directly as wires, faces, and boxes. This is less parametric but much more scriptable. For this tube house project, Draft + Part is entirely sufficient.

### Gap 4: No undo through MCP

If `execute_code` creates objects you don't want, there's no MCP tool to undo.

**Workaround:** Use `delete_object` to remove unwanted objects by label. Or close the document without saving and reopen/regenerate. Build a habit of saving before each experimental prompt: `doc.save()`.

### Gap 5: FreeCAD must be running (no headless MCP)

The MCP server requires a live FreeCAD GUI instance with the RPC server running. You can't use it in a headless server environment.

**Workaround for headless use:** Use `freecadcmd generate_floorplan.py` (FreeCAD command-line mode) instead of MCP. This runs the full Python script headlessly. Good for CI/CD or batch regeneration.

### Gap 6: Screenshots via `get_view` can be large

When using Claude via API (not opencode), large screenshots eat into your context window and cost tokens.

**Workaround:** Use `--only-text-feedback` in `opencode.json`, and instead rely on `get_objects` to verify the model state. Only use `get_view` when you need a visual sanity check.

### Gap 7: API property names differ from documentation / other CAD software

As noted in `docs/lessons-learned.md`: FreeCAD uses `DrawStyle` not `LineStyle`, uses `(R, G, B)` float tuples not hex colours, and so on. LLMs trained on mixed CAD documentation sometimes suggest wrong property names.

**Workaround:** Keep `docs/lessons-learned.md` updated and paste it into your opencode session as context at the start. This "trains" the LLM on this project's known quirks for the session.

---

## Part 6 — Suggested Improvements to This Repo

### 1. Add a session starter prompt file

Create `docs/session-starter.md` with the context block (coordinate system, project state, known API quirks) so you can paste it once at the start of every opencode or Claude session instead of retyping it.

### 2. Extend `generate_floorplan.py` for 3D stacking

Add a `draw_building_massing()` function that reads all floors from the spec and stacks them at the correct Z height in a single `Tubehouse_3D_Massing.FCStd` document. This removes the need to do it interactively via MCP each time.

### 3. Add F3 and F4 to `floorplan-spec.json`

The spec currently has F0–F2. Following the same schema, add:
- **F3** (floor level 3): Master suite + study / Master bathroom
- **F4** (floor level 4): Rooftop terrace + plant room

Use the SVG-first workflow documented in `docs/lessons-learned.md` (Lesson 2).

### 4. Add a Claude Desktop config option

The guide currently only covers opencode. Many users will want to use Claude Desktop directly. Add a section covering `claude_desktop_config.json` setup:

```json
{
  "mcpServers": {
    "freecad": {
      "command": "uvx",
      "args": ["freecad-mcp"]
    }
  }
}
```

This lives at `~/Library/Application Support/Claude/claude_desktop_config.json` (Mac) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows).

### 5. Add a `Makefile` or `run.bat` for one-click regeneration

```bat
@echo off
echo Running FreeCAD floorplan generator...
freecadcmd src\generate_floorplan.py
echo Done. Check output\ folder.
pause
```

This removes the need to open FreeCAD manually every time for batch regeneration.

### 6. Capture more lessons learned

After every FreeCAD session, add a new entry to `docs/lessons-learned.md`. Future sessions (and future LLM context) benefit enormously from a growing list of "don't do X, do Y instead" notes specific to this project.

---

## Part 7 — Comparison: Claude vs Gemini vs Other LLMs

| | Claude Sonnet 4.x | Gemini 2.5 Pro | GPT-4o | Local (Ollama) |
|---|---|---|---|---|
| **Code quality** | Excellent | Very good | Good | Variable |
| **Context window** | 200K tokens | 1M tokens | 128K tokens | Usually 32–128K |
| **FreeCAD API accuracy** | Good (needs prompting) | Good (needs prompting) | OK | Usually weak |
| **Multi-step reasoning** | Excellent | Excellent | Good | Weak |
| **Cost** | Mid | Low–mid | Mid | Free |
| **Best for** | Everything | When context > 200K needed | Fallback | Privacy / offline |

**In practice for this project:** Claude and Gemini are roughly equivalent for FreeCAD Python generation. The key variable is **context window** — if you paste the entire `floorplan-spec.json` (which is large) plus the full `generate_floorplan.py` script plus lessons learned, you approach 50,000 tokens of context. Both Claude and Gemini handle this comfortably. GPT-4o starts to struggle.

**Gemini was used** to generate the original `reference/gemini_original.html` layout and the initial SVG preview. Claude has been used for the script development and MCP integration. Either works well. Use whichever you have an API key for.

**One practical advantage of Claude Desktop over opencode:** Claude Desktop is a GUI application — easier for non-technical users. opencode requires terminal comfort. Both support MCP, both work with the `freecad-mcp` server.

---

## Part 8 — End-to-End Beginner Workflow (Condensed)

Here is the complete day-1 workflow from zero to your first AI-generated tube house floor plan:

**One-time setup (30 minutes):**
1. Install FreeCAD → install MCP addon → verify "Start RPC Server" works
2. Install `uv` (`pip install uv`) and `opencode` (`npm install -g @opencode-ai/opencode`)
3. Run `opencode` once, enter your Anthropic or Google API key
4. In this project folder, verify: `opencode mcp list` shows `freecad: connected`

**Each working session:**
1. Open FreeCAD → Workbench: "MCP Addon" → click "Start RPC Server"
2. Open a terminal in this project folder → run `opencode`
3. Paste the starter context block (coordinate system, project state)
4. Start with: *"Show me what floors are currently in floorplan-spec.json and what's in the output folder"*
5. Work floor by floor: design → SVG preview → add to spec → run script → verify output

**For interactive 3D work via MCP:**
1. Ask Claude to create a new document and draw one element at a time
2. Use `get_view` to check screenshots after each step
3. When happy, ask Claude to save the document
4. Build up the full `generate_floorplan.py` script from these interactive experiments

---

## Appendix: Known FreeCAD API Gotchas

These are pulled from `docs/lessons-learned.md` and other known issues:

| Wrong | Correct | Notes |
|-------|---------|-------|
| `obj.ViewObject.LineStyle = "Dashed"` | `obj.ViewObject.DrawStyle = "Dashed"` | FreeCAD uses DrawStyle |
| `obj.ViewObject.Color = "#FF0000"` | `obj.ViewObject.ShapeColor = (1.0, 0.0, 0.0)` | RGB floats, not hex |
| `Draft.makeRectangle(w, h)` | `Draft.makeWire([pts], closed=True, face=True)` | makeRectangle has placement quirks |
| `doc.save()` without `doc.recompute()` | Always `doc.recompute()` first | Otherwise changes may not be stored |
| `FreeCAD.Vector(x, y)` | `FreeCAD.Vector(x, y, 0)` | Always pass Z explicitly |
| `importDXF` used in regular Python | Must run inside FreeCAD | importDXF is a FreeCAD-only module |
| `obj.Label = "My Wall"` | `obj.Label = "My_Wall"` | Spaces in labels can cause DXF issues |

---

*Last updated: 2026-03-21 | Repo: freecad-floorplan | Project: 4×25m nhà ống, Hà Nội*
