# Plan: Generate 2nd Floor (Level 1) — Living Room + Kitchen

## Context
Ground floor is complete and published to GitHub. The next step is a 2nd floor (level 1) with a **living room** and **kitchen**, while keeping the repeating core elements (stairs, lift, light wells). The workflow is: SVG preview first -> review in Chrome -> then add to JSON spec so `generate_floorplan.py` produces the FreeCAD output.

## User Decisions
- **Living zone**: One open-plan space (not split into living + dining)
- **Front wall**: Full 200mm wall with windows (not open railing)

## 2nd Floor Layout Design

Same 4x25m envelope. The **core zone** (y=15000-19000) and **rear light well** (y=23000-25000) repeat identically from ground floor. The front and rear habitable zones change:

### Zone breakdown (Y axis)
| Zone | Y range | Depth | Use on Floor 1 |
|------|---------|-------|-----------------|
| Front balcony | 0-2000 | 2000mm | Enclosed balcony (street-facing, full front wall + windows) |
| Living room | 2000-15000 | 13000mm | Open-plan living + dining (46.8 m2) |
| Core | 15000-19000 | 4000mm | Lift + Stairs + Light well (same as GF) |
| Kitchen + WC | 19000-23000 | 4000mm | Kitchen (left 2150mm) + Bathroom (right 1350mm) |
| Rear void | 23000-25000 | 2000mm | Rear light well (same as GF) |

### Wall layout differences vs ground floor
- **Full front wall** at y=0 (200mm thick, full 4000mm width) with 2 window openings
  - Window 1: x=600-1400 (800mm wide)
  - Window 2: x=2600-3400 (800mm wide)
- **Balcony partition** at y=2000 (100mm) with sliding door opening (x=700-2700, 2000mm wide)
- **No partition at y=5000** -- living room is one continuous open space (2100-14900)
- **Living/core partition** at y=15000 stays same
- **Core/kitchen partition** at y=19000 with door opening (same position as GF)
- **Kitchen/rear partition** at y=23000 with door opening (same as GF)
- **Core vertical walls** identical (lift separator, stair separator)
- **Kitchen/bathroom wall** at x=2350 (same as GF utility/bath wall)

### Rooms
| Room | x | y | w | h | Area |
|------|---|---|---|---|------|
| Balcony | 200-3800 | 200-2000 | 3600x1800 | 6.5 m2 |
| Living Room | 200-3800 | 2100-14900 | 3600x12800 | 46.1 m2 |
| Lift Shaft | 200-1000 | 15100-19000 | 800x3900 | 3.1 m2 |
| Staircase | 1100-2700 | 15100-19000 | 1600x3900 | 6.2 m2 |
| Light Well | 2800-3800 | 15100-19000 | 1000x3900 | 3.9 m2 |
| Kitchen | 200-2350 | 19100-23000 | 2150x3900 | 8.4 m2 |
| Bathroom | 2450-3800 | 19100-23000 | 1350x3900 | 5.3 m2 |
| Rear Light Well | 200-3800 | 23100-24800 | 3600x1700 | 6.1 m2 |

### Elements
- Stairs, lift, light wells -- identical to GF
- Kitchen sink at rear of kitchen zone (x=200, y=22250)
- Toilet in bathroom (same position as GF)
- Sliding door to balcony (new door type: `"sliding"`)

### Doors
1. **Balcony sliding door** -- x=700-2700, y=2000 (2000mm wide sliding, through partition)
2. **Core -> kitchen door** -- same position as GF core->utility door (x=1100-1900, y=19100)
3. **Kitchen -> rear door** -- same position as GF rear door (x=200-1000, y=23100)

### Windows (new element type for upper floors)
1. **Front window L** -- x=600-1400, y=0 (800mm wide, in front wall)
2. **Front window R** -- x=2600-3400, y=0 (800mm wide, in front wall)

## Implementation Steps

### Step 1: Create SVG preview -- `output/svg/floor_1_preview.svg`
Hand-craft an SVG file based on `reference/floor_0_ground.svg` structure:
- Same viewBox, defs, grid, dimension lines, title block format
- Title: "FIRST FLOOR PLAN" / Sheet A-102
- Changed zones: balcony (front), living room (main), kitchen (behind core)
- Core zone drawn identically
- Sliding door symbol for balcony (two parallel lines instead of arc)
- Window symbols in front wall (gaps in wall with thin lines at edges)
- Kitchen fixtures: sink (rectangle + circle drain)

### Step 2: Open SVG in Chrome for review
Open the SVG in Chrome tab for user to review layout before committing to JSON spec.

### Step 3: Add floor 1 to `spec/floorplan-spec.json`
Add a second entry in the `"floors"` array with level 1, containing all zones, walls, rooms, elements, doors, and labels following the exact same schema as floor 0.

### Step 4: Update `src/generate_floorplan.py`
Add handlers for new element/door types:
- `"sliding"` door type: draw as two parallel lines (instead of leaf + arc)
- `"window"` element type: draw as gap in wall with thin perpendicular lines at edges

### Step 5: Run in FreeCAD
User runs the script -- it will now process both floors and output:
- `output/fcstd/floorplan_F1.FCStd`
- `output/dxf/floorplan_F1.dxf`
- `output/svg/freecad_F1.svg`

## Files to create/modify
| File | Action |
|------|--------|
| `output/svg/floor_1_preview.svg` | **Create** -- hand-crafted SVG preview |
| `spec/floorplan-spec.json` | **Edit** -- add floor 1 object to `floors[]` |
| `src/generate_floorplan.py` | **Edit** -- add `"sliding"` door type + `"window"` element type handlers |

## Verification
1. Open `floor_1_preview.svg` in Chrome -- visually confirm layout
2. Validate JSON with `python -c "import json; ..."`
3. Run script in FreeCAD -- should produce F0 + F1 outputs
4. Compare F1 SVG with preview to confirm match
