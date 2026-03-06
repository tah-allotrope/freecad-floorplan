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
