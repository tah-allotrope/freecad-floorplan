# FreeCAD Scripting Lessons Learned

## Lesson 1: `DrawStyle` vs `LineStyle` for line appearance

**Date:** 2026-03-06
**Error:**
```
AttributeError: 'PartGui.ViewProviderPartExt' object has no attribute 'LineStyle'
```

**Root Cause:**
FreeCAD's `ViewObject` (the visual representation of a Part object) does not have a property called `LineStyle`. The correct property name is `DrawStyle`.

**Wrong:**
```python
obj.ViewObject.LineStyle = "Dashed"
obj.ViewObject.LineStyle = "Dashdot"
```

**Correct:**
```python
obj.ViewObject.DrawStyle = "Dashed"
obj.ViewObject.DrawStyle = "Dashdot"
```

**Valid `DrawStyle` values:**
| Value       | Appearance                  |
|-------------|-----------------------------|
| `"Solid"`   | Continuous line (default)   |
| `"Dashed"`  | Evenly spaced dashes        |
| `"Dotted"`  | Evenly spaced dots          |
| `"Dashdot"` | Alternating dash and dot    |

**Other useful `ViewObject` appearance properties:**
| Property      | Type              | Example                        |
|---------------|-------------------|--------------------------------|
| `LineColor`   | `(R, G, B)` float | `(0.58, 0.77, 0.99)` light blue |
| `LineWidth`   | float             | `2.0`                          |
| `DrawStyle`   | string            | `"Dashed"`                     |
| `ShapeColor`  | `(R, G, B)` float | `(1.0, 0.0, 0.0)` red         |
| `Transparency` | int (0-100)      | `50`                           |
| `Visibility`  | bool              | `True` / `False`               |

**Takeaway:** When AI (Gemini, ChatGPT, etc.) generates FreeCAD scripts, always verify property names against the FreeCAD Python API. Common naming mismatches like `LineStyle`/`DrawStyle` are a frequent source of errors because training data may mix up CAD software APIs (AutoCAD uses `LineStyle`, FreeCAD uses `DrawStyle`).

---

## Lesson 2: Multi-floor workflow — SVG preview before JSON spec

**Date:** 2026-03-06

**Pattern:** For each new floor:
1. Hand-craft SVG preview first (`output/svg/floor_N_preview.svg`)
2. Open in browser for visual review (use `python -m http.server` since `file://` doesn't work with Chrome extensions)
3. Once approved, add floor to `spec/floorplan-spec.json`
4. Run FreeCAD script — it auto-processes all floors in the spec

**Why:** SVG is fast to iterate on visually. JSON spec is the source of truth for FreeCAD. Keeping them separate means you can review layout before committing to the CAD pipeline.

---

## Lesson 3: Repeating elements across floors — keep a consistent core

**Date:** 2026-03-06

**Pattern:** In a tubehouse, these elements repeat identically on every floor:
- Core zone (lift + stairs + light well) at y=15000-19000
- Rear light well at y=23000-25000
- Exterior side walls (left, right, rear)
- Core vertical separator walls (x=1000, x=2700)
- Behind-core zone split wall at x=2350 (structural alignment)

**Takeaway:** When adding a new floor, copy the core zone spec verbatim. Only the front zone (y=0-15000) and behind-core usage (y=19000-23000) change per floor. This saves time and ensures structural consistency.

---

## Lesson 4: New element/door types require Python handler updates

**Date:** 2026-03-06

**Pattern:** The FreeCAD script (`generate_floorplan.py`) processes elements and doors by type. When introducing a new type:
- **Sliding door** (`"sliding"`): Two parallel lines for tracks. Spec needs `x`, `y`, `width_mm`, `wall_thickness_mm`.
- **Window** (`"window"`): Glass center line + perpendicular ticks at edges. Spec needs `x`, `y`, `width_mm`, `wall_thickness_mm`.

**Also:** New room IDs need color entries in `FILL_COLORS` dict, otherwise they default to white `(1,1,1)`.

---

## Lesson 5: Chrome `file://` URLs don't work with browser automation extensions

**Date:** 2026-03-06

**Problem:** Chrome extensions (MCP, Claude-in-Chrome) cannot navigate to `file:///` URLs — they get rewritten as `https://file///...` which fails.

**Solution:** Start a local HTTP server:
```bash
cd output/svg && python -m http.server 8765
```
Then navigate to `http://localhost:8765/floor_1_preview.svg`.

---

## Lesson 6: Bedroom floor layout — pass-through vs corridor trade-off

**Date:** 2026-03-06

**Context:** 4m-wide tubehouse, 3.6m clear interior width.

**Options considered:**
1. **Side corridor** (800-1000mm): Each room has its own door, private. But corridor eats 10+ m² and rooms shrink to 2.5-2.7m width.
2. **Pass-through rooms** (no corridor): Full 3.6m width per room. Rooms connect via doors in partition walls. Less private but maximizes space.

**Decision:** Pass-through layout chosen. Room ordering matters for privacy:
- Entry from core → least-private room first (small bedroom / transition room)
- Master bedroom in the middle (more private)
- Working room at front (most private, only passage to balcony)

**Takeaway:** In narrow tubehouses, always consider room ordering from the core/stairs entry point. The first room from stairs is the least private.
