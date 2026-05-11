# Research Brief: FreeCAD-to-Blender Floorplan-to-3D Workflow Landscape

**Date:** 2026-05-11
**Status:** Complete
**Scope:** Domain tools, interchange formats, codebase analysis, and improvement opportunities for the FreeCAD→Blender architectural visualization pipeline.

---

## Table of Contents

1. [Codebase Architecture Analysis](#1-codebase-architecture-analysis)
2. [Established Parametric Floor Plan → 3D Patterns](#2-established-parametric-floor-plan--3d-patterns)
3. [IFC Interoperability: FreeCAD ↔ Blender (2025-2026)](#3-ifc-interoperability-freecad--blender-2025-2026)
4. [Interchange Format Trade-offs](#4-interchange-format-trade-offs)
5. [Procedural/Parametric Building Generators](#5-proceduralparametric-building-generators)
6. [Professional Arch-Viz Pipeline Patterns](#6-professional-arch-viz-pipeline-patterns)
7. [Key Findings & Recommendations](#7-key-findings--recommendations)
8. [Sources](#8-sources)

---

## 1. Codebase Architecture Analysis

### 1.1 Data Flow Overview

The current pipeline follows a **linear, spec-driven** architecture:

```
spec/floorplan-spec.json
        │
        ▼
src/generate_floorplan.py  ──→  FreeCAD (.FCStd, .DXF, .SVG, .OBJ)
        │                                    │
        │                                    ▼
        │                         src/blender_export_utils.py  ──→  OBJ + MTL
        │                                    │
        │                                    ▼
        │                         src/setup_blender_scene.py   ──→  .blend
        │                                    │
        │                                    ▼
        │                         src/render_blender.py        ──→  .png
        │
spec/blender_materials.json  ──→  Material assignment config
```

### 1.2 Spec Format (`spec/floorplan-spec.json`)

**Structure:**
- **Project metadata** — plot width/depth (4000 × 25000 mm), 5 floors
- **Per-floor definition** — each floor contains:
  - `zones[]` — spatial zones with y_start/y_end (depth partitioning)
  - `walls[]` — explicit wall rectangles with x, y, w, h (axis-aligned only)
  - `rooms[]` — room fills with id, name, area_sqm
  - `elements[]` — stairs, lifts, light wells, toilets, sinks, windows, pergola, planters, solar panels
  - `doors[]` — swing (leaf + arc), sliding, garage_opening
  - `labels[]` — text annotations with position and size

**Key characteristics:**
- All coordinates in mm, axis-aligned rectangles only
- Walls are axis-aligned boxes — no diagonal or curved walls
- Doors contain pre-computed arc geometry (leaf endpoints, arc center/radius/angles)
- No window 3D geometry (only 2D symbols in plan)
- No roof geometry (only rooftop plan elements)
- Core zone (lift + staircase + light well) is consistent across all 5 floors at Y=15000-19000

### 1.3 FreeCAD Geometry Generation (`src/generate_floorplan.py`)

**Approach:** Direct Part/Draft API calls — NOT using FreeCAD's Arch/BIM workbench.

| Element | FreeCAD API | 2D | 3D |
|---------|------------|-----|-----|
| Walls | `Draft.makeWire` (closed, face=True) + `Part::Box` | ✅ | ✅ (extruded box) |
| Rooms | `Draft.makeWire` (closed, face=True) | ✅ | ❌ |
| Slabs | `Part::Box` | ❌ | ✅ (200mm thick) |
| Stairs | `Draft.makeLine` + `Part::Box` per tread | ✅ | ✅ (individual step boxes) |
| Lift | `Draft.makeLine` (X pattern) | ✅ | ❌ |
| Windows | `Draft.makeLine` (glass + ticks) | ✅ | ❌ |
| Doors | `Draft.makeLine` + `Draft.makeCircle` (arc) | ✅ | ❌ |
| Sanitary | `Draft.makeWire` + `Draft.makeCircle` | ✅ | ❌ |

**Stacking** (`stack_floors()`): Creates a combined document, re-generates 3D walls + slabs per floor with cumulative Z offsets from `floorplan_utils.cumulative_floor_offsets()`.

**Facade** (`draw_front_facade()`): Separate document generating 2D elevation view with floor bands, openings (windows/doors), and balcony railings.

### 1.4 OBJ Export (`src/blender_export_utils.py`)

**Strategy:** Custom mesh export via FreeCAD's `Mesh` module.

- Triangulates each Part solid via `Mesh.Mesh(shape)`
- Writes Wavefront OBJ with named groups (`g`) per object
- Material inference by keyword matching in object labels (`_infer_material_key()`)
- Convention: `F{level}_{type}` group names (e.g., `F0_wall`, `F1_slab`)
- Separate MTL file with flat diffuse colors only

**Limitations:**
- No normals export (relies on Blender auto-smooth)
- No UV coordinates
- No texture paths
- Material inference is fragile (keyword-based string matching)
- Exports all shapes including 2D wires (which have no faces)

### 1.5 Material System (`src/blender_materials.py`)

**Three-tier mapping:**
1. `ROOM_MATERIAL_MAP` — room ID → material name (e.g., `bathroom` → `Tile_Bathroom`)
2. `ZONE_MATERIAL_MAP` — zone ID → material name
3. `OBJ_GROUP_MATERIAL_MAP` — OBJ group convention key → material name

**Material definitions:** 10 PBR materials with base_color, roughness, metallic, and optional transmission (for glass). Created in Blender via Principled BSDF nodes.

### 1.6 Blender Scene Assembly (`src/setup_blender_scene.py`)

- Imports OBJ via `bpy.ops.wm.obj_import` (Blender 4.x) or `bpy.ops.import_scene.obj` (3.x)
- Falls back to STL if OBJ unavailable
- Assigns materials by matching OBJ group name keywords against config
- Adds Sun + Area fill light from JSON config
- Adds camera with auto-targeting to building centroid
- Saves as `.blend`

### 1.7 Render Pipeline (`src/render_blender.py`)

- Cycles engine with configurable samples (default 128)
- 1920×1080 PNG output
- Headless: `blender --background scene.blend --python render_blender.py`

---

## 2. Established Parametric Floor Plan → 3D Patterns

### 2.1 FreeCAD Arch/BIM Workbench

**Official API** (from Context7 FreeCAD docs):
FreeCAD's BIM workbench provides `Arch.*` functions that create parametric building elements with built-in IFC semantics:

```python
import Arch, Draft
# Walls from baseline with proper joinery
wall = Arch.makeWall(baseline_wire, height=3000, width=200)
# Windows/doors hosted in walls with automatic opening subtraction
window = Arch.makeWindowPreset("Open 2-pane", width=1200, height=1500, ...)
window.Hosts = [wall]
# Slabs from outline
slab = Arch.makeStructure(outline_wire, height=200)
slab.IfcType = "Slab"
# Hierarchical: Site → Building → Floor → [Walls, Windows, ...]
```

**Key advantages over current codebase approach:**
- Walls automatically join and subtract openings
- Windows/doors hosted in walls create proper 3D voids
- IFC metadata embedded (IfcType, properties)
- Built-in wall types (exterior, interior) with different thicknesses
- `Arch.makeFloor()` provides proper storey grouping
- Native export to IFC via the NativeIFC workbench

**Current gap:** The codebase uses raw `Part::Box` for walls instead of `Arch.makeWall()`, which means:
- No automatic opening subtraction for windows/doors
- No IFC metadata
- No parametric wall joinery
- No wall type differentiation (exterior vs partition)

### 2.2 Blender Architectural Add-ons

| Add-on | Purpose | Relevance |
|--------|---------|-----------|
| **Archimesh** | Room/house modeling from 2D parameters | Moderate — manual room-by-room approach |
| **Archipack** | Parametric roofs, walls, floors, stairs, windows | High — procedural generation from parameters |
| **Bonsai** (formerly BlenderBIM) | Native IFC authoring in Blender | Critical — IFC interchange |
| **Sverchok** | Node-based generative geometry | High — visual parametric pipeline |
| **Architecture Nodes** | Geometry Nodes-based building generation | Moderate — Blender 4.x GN approach |

### 2.3 Pattern Comparison

| Pattern | Tools | Data Source | Parametric? | IFC? | 3D Quality |
|---------|-------|-------------|-------------|------|-----------|
| **Spec→Part::Box (current)** | FreeCAD | JSON spec | Semi (re-run spec) | ❌ | Low (boxes) |
| **Spec→Arch API** | FreeCAD | JSON spec | ✅ (FreeCAD params) | ✅ | Medium |
| **Spec→Arch→IFC→Bonsai** | FreeCAD + Blender | JSON spec → IFC | ✅ (bidirectional) | ✅ | High |
| **Archipack nodes** | Blender only | Blender UI | ✅ (Blender params) | ❌ | Medium |
| **Sverchok/Geometry Nodes** | Blender only | Node graph | ✅ (visual) | ❌ | Variable |

---

## 3. IFC Interoperability: FreeCAD ↔ Blender (2025-2026)

### 3.1 FreeCAD Side: NativeIFC Workbench

**Status (FreeCAD 1.0+):**
- FreeCAD's BIM workbench includes a `NativeIFC` module built on IfcOpenShell
- Documents can be natively saved/loaded as `.ifc` files
- All Arch elements (walls, slabs, windows, doors) carry IFC type metadata
- FreeCAD can open IFC files directly, edit them, and save back
- Export via `importIFC` module or NativeIFC workbench

**Python API:**
```python
# FreeCAD Arch approach (would replace current Part::Box)
import Arch
wall = Arch.makeWall(length=4000, width=200, height=3500)
wall.IfcType = "Wall"  # Embedded IFC metadata
# Export to IFC
import exportIFC
exportIFC.export(doc.Objects, "building.ifc")
```

### 3.2 Blender Side: Bonsai (formerly BlenderBIM)

**Status (v0.8.5, May 2026):**
- Renamed from "BlenderBIM" to **Bonsai** in 2024
- Built on IfcOpenShell (LGPL-3.0), 2.5k GitHub stars
- Provides full native IFC authoring in Blender
- Supports IFC2x3, IFC4 Add2, IFC4x3 schemas
- Can create walls, slabs, doors, windows, rooms directly in IFC
- Drawing generation, structural analysis, cost scheduling, FM
- Active development with frequent alpha releases

**Bonsai Capabilities for this project:**
- Import IFC from FreeCAD with full spatial hierarchy
- Walls with proper material layers
- Windows/doors as hosted openings
- Room/space definitions with boundaries
- Building storey organization
- 2D drawing generation from IFC models

### 3.3 IFC Interchange Status Summary

| Direction | Status | Quality | Notes |
|-----------|--------|---------|-------|
| FreeCAD → IFC | ✅ Good | High | NativeIFC + Arch workbench |
| IFC → Blender (Bonsai) | ✅ Good | High | Native IFC parsing via IfcOpenShell |
| Blender (Bonsai) → IFC | ✅ Good | High | Full authoring support |
| IFC → FreeCAD | ✅ Good | Medium | NativeIFC import works |
| Round-trip fidelity | ⚠️ Medium | — | Complex geometry may lose parametric data |

**Key limitation:** The current codebase does NOT use IFC at all. It bypasses FreeCAD's Arch/BIM workbench entirely, using raw Part::Box primitives. This means the entire IFC ecosystem is currently inaccessible.

---

## 4. Interchange Format Trade-offs

### 4.1 Comparison Table

| Format | Geometry | Materials | Hierarchy | IFC Semantics | UV/Textures | Normals | Anim | File Size | Blender Import | FreeCAD Export |
|--------|----------|-----------|-----------|---------------|-------------|---------|------|-----------|----------------|----------------|
| **OBJ + MTL** | ✅ Mesh | ✅ Basic Kd/Ks | Group names only | ❌ | ❌ (no UVs in current) | ⚠️ Optional | ❌ | Small | ✅ Native | ✅ Custom |
| **FBX** | ✅ Mesh | ✅ PBR-ready | ✅ Objects/Collections | ❌ | ✅ | ✅ | ✅ | Medium | ✅ Native | ❌ (no built-in) |
| **IFC** | ✅ B-rep + CSG | ✅ Layered | ✅ Spatial (Site→Storey→Element) | ✅ Full | ⚠️ Limited | ⚠️ | ❌ | Large | ✅ Bonsai | ✅ NativeIFC |
| **glTF 2.0** | ✅ Mesh | ✅ PBR (metallic-roughness) | ✅ Scene graph | ❌ | ✅ | ✅ | ✅ | Small | ✅ Native | ❌ (via IfcConvert) |
| **DAE (Collada)** | ✅ Mesh | ✅ Basic | ✅ Scene graph | ❌ | ✅ | ✅ | ✅ | Large | ✅ Native | ⚠️ Experimental |
| **STL** | ✅ Mesh only | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | Medium | ✅ Native | ✅ Built-in |
| **STEP** | ✅ B-rep (exact) | ❌ | ❌ | ❌ | ❌ | N/A | ❌ | Medium | ⚠️ (CAD Sketcher) | ✅ Built-in |
| **USD** | ✅ Mesh | ✅ MaterialX/UsdPreviewSurface | ✅ Stage hierarchy | ❌ | ✅ | ✅ | ✅ | Medium | ✅ Native (4.0+) | ❌ |

### 4.2 Recommendations for This Project

| Use Case | Best Format | Rationale |
|----------|-------------|-----------|
| **Current visualization pipeline** | OBJ + MTL (keep) | Simple, works, low overhead |
| **Upgrade path for better materials** | FBX | PBR materials, normals, UVs, collections |
| **Architectural collaboration** | IFC | Industry standard, round-trip with Revit/ArchiCAD |
| **Web/interactive viewers** | glTF 2.0 | Compact, PBR, GPU-friendly, three.js/Cesium |
| **Manufacturing/CNC** | STEP | Exact B-rep geometry |
| **Rapid prototyping** | STL | Universal mesh format |

### 4.3 OBJ Limitations in Current Codebase

1. **No normals** — `blender_export_utils.py` writes only vertices and faces
2. **No UVs** — No texture mapping data
3. **Basic MTL** — Only diffuse + specular colors, no textures or PBR
4. **Group names as material keys** — Fragile naming convention
5. **2D wire export** — Lines/wires with no faces pollute the OBJ
6. **Scale conversion** — FreeCAD uses mm, Blender uses m; the OBJ carries raw mm values

---

## 5. Procedural/Parametric Building Generators

### 5.1 Existing Tools & Projects

| Tool/Project | Approach | Tech | Relevance |
|-------------|----------|------|-----------|
| **Archipack** (Blender add-on) | Parametric walls, roofs, stairs from UI params | Blender Python | High — could consume spec JSON |
| **Building Generator** (Blender) | CGA-style rule-based facade generation | Blender Python | Medium — facade detail |
| **Sverchok + ifcsverchok** | Visual node programming for IFC | Blender + IfcOpenShell | High — data-driven pipeline |
| **FreeCAD BIM workbench** | Parametric Arch elements | FreeCAD Python | High — natural upgrade path |
| **CityEngine / CGA** | Rule-based procedural modeling | Esri (commercial) | Low — not open source |
| **Compas / Volomit** | Python-based AEC computation | Python (Rhino/Blender) | Medium — research-grade |
| **Honeybee/Ladybug** | Environmental analysis from geometry | Python + Grasshopper | Low — analysis, not generation |
| **IfcOpenShell Python API** | IFC manipulation from Python | Pure Python | High — could generate IFC directly |

### 5.2 Spec-to-IFC Pattern (Most Relevant)

The most direct improvement path: **Read JSON spec → Generate IFC directly via IfcOpenShell Python API**

```python
import ifcopenshell
import ifcopenshell.api

model = ifcopenshell.api.run("project.create_file")
project = ifcopenshell.api.run("root.create_entity", model, ifc_class="IfcProject")
# ... create sites, buildings, storeys, walls, slabs from spec JSON
```

This bypasses FreeCAD entirely for geometry generation and produces industry-standard IFC that Bonsai can open directly in Blender with full spatial hierarchy and semantic data.

### 5.3 Geometry Nodes Approach (Blender 4.x)

Blender's Geometry Nodes could consume the spec JSON directly:

```
JSON Spec → Python driver → Geometry Nodes modifier tree
    ├── Floor slab instances
    ├── Wall curves → extrude
    ├── Window/door openings → boolean difference
    └── Material assignment by attribute
```

**Advantages:** Real-time parametric updates, no file interchange needed, native Blender.
**Disadvantages:** Complex node tree maintenance, no IFC output, single-tool lock-in.

---

## 6. Professional Arch-Viz Pipeline Patterns

### 6.1 Typical Studio Workflows

**Pattern A: BIM-Centric (Architecture Firms)**
```
Revit/ArchiCAD → IFC → Blender (Bonsai) → Cycles render
                  └→ Navisworks (clash detection)
```

**Pattern B: FreeCAD Open-Source Pipeline**
```
FreeCAD BIM → IFC → Bonsai (Blender) → Cycles/Eevee render
     └→ NativeIFC round-trip edits
```

**Pattern C: Direct Modeling (Visualization Studios)**
```
Architect's DWG/DXF → Manual Blender modeling → Custom materials → Render
```

**Pattern D: Procedural (Emerging)**
```
JSON/Python spec → IfcOpenShell → IFC → Bonsai → Render
                  └→ Direct Blender Python → bpy ops → Render
```

### 6.2 Best Practices for FreeCAD → Blender

1. **Use Arch workbench for geometry** — enables IFC export and parametric edits
2. **Export IFC for interchange** — preserves spatial hierarchy and semantic data
3. **Use glTF for web previews** — compact, PBR-ready
4. **Apply materials in Blender** — FreeCAD materials are basic; Blender's Principled BSDF is superior
5. **Add HDRI environment** — for realistic lighting instead of flat sun/fill
6. **Use compositing nodes** — for post-processing (bloom, color grading)
7. **Normal maps from geometry** — add surface detail without extra geometry

### 6.3 Common Pain Points

- **Scale mismatch:** FreeCAD mm → Blender m requires /1000 scaling
- **Material loss:** IFC materials are structural, not visual; need remapping
- **Missing openings:** If walls are boxes (not Arch walls), windows/doors don't cut voids
- **Flat geometry:** Box-only walls look terrible without bevels, edge wear, or texture
- **No exterior context:** Building floating in void needs ground plane, street, neighbors

---

## 7. Key Findings & Recommendations

### 7.1 Current State Assessment

| Aspect | Rating | Notes |
|--------|--------|-------|
| Data spec | ✅ Good | Well-structured JSON, 5 floors, comprehensive |
| FreeCAD generation | ⚠️ Adequate | Uses raw Part::Box, not Arch/BIM |
| OBJ export | ⚠️ Adequate | Custom mesh export, no normals/UVs |
| Material system | ✅ Good | 3-tier mapping, Principled BSDF, JSON sidecar |
| Scene assembly | ✅ Good | Clean import, lighting, camera |
| Render pipeline | ✅ Good | Cycles headless, configurable |
| IFC/BIM awareness | ❌ Missing | No IFC export, no Arch elements |
| 3D window/door geometry | ❌ Missing | Only 2D symbols |
| Roof geometry | ❌ Missing | Only rooftop plan |
| Exterior/landscaping | ❌ Missing | Building in void |

### 7.2 Improvement Opportunities (Priority Order)

1. **Migrate walls from Part::Box to Arch.makeWall()** — unlocks window/door voids, IFC export, parametric editing
2. **Add IFC export path** — use NativeIFC or direct IfcOpenShell Python for IFC output
3. **Add 3D window/door geometry** — Arch.makeWindowPreset() / Arch.makeWindow() with proper host wall subtraction
4. **Add normals + UVs to OBJ export** — dramatically improves Blender shading quality
5. **Filter 2D-only objects from OBJ** — skip wires, lines, text from 3D export
6. **Add glTF export** — via IfcConvert (IFC→glTF) or Blender Python for web viewing
7. **Consider direct IfcOpenShell generation** — bypass FreeCAD geometry entirely, generate IFC from spec JSON

### 7.3 Recommended Upgrade Path

**Phase 1 (Low effort, high impact):**
- Fix OBJ export: add normals, filter 2D objects, fix scale
- Add ground plane to Blender scene
- Add HDRI environment lighting

**Phase 2 (Medium effort, high impact):**
- Migrate to FreeCAD Arch API for walls, windows, doors
- Enable IFC export via NativeIFC
- Add Bonsai as IFC viewer alternative

**Phase 3 (High effort, transformative):**
- Direct IFC generation from spec JSON via IfcOpenShell
- Full BIM round-trip capability
- Geometry Nodes procedural facades

---

## 8. Sources

### Codebase Analysis (Primary)
- `src/generate_floorplan.py` — FreeCAD geometry generation (1007 lines)
- `src/blender_export_utils.py` — OBJ/MTL export (252 lines)
- `src/blender_materials.py` — Material definitions (198 lines)
- `src/setup_blender_scene.py` — Blender scene assembly (296 lines)
- `src/render_blender.py` — Cycles render pipeline (118 lines)
- `src/floorplan_utils.py` — Pure helper functions (23 lines)
- `src/facade_utils.py` — Facade derivation helpers (84 lines)
- `spec/floorplan-spec.json` — Building data (3108 lines)
- `spec/blender_materials.json` — Material config sidecar (77 lines)

### Context7 Documentation
- **FreeCAD** (`/freecad/freecad`) — Official FreeCAD Python API docs including Arch/BIM workbench with `Arch.makeWall()`, `Arch.makeWindowPreset()`, `Arch.makeStructure()`, `Arch.makeFloor()`, `Arch.makeSite()`, NativeIFC module, and IFC export capabilities. 558 code snippets, high source reputation.
- **Blender Python API** (`/websites/blender_api_4_5`) — Blender 4.5 API with `bpy.ops.wm.obj_import`, `bpy.ops.wm.fbx_import`, `bpy.ops.export_scene.gltf`, Principled BSDF node setup, and USD MaterialX import hooks. 19,386 code snippets.

### Web Sources
- **Bonsai (formerly BlenderBIM)** — https://bonsaibim.org — v0.8.5, open-source IFC authoring platform for Blender built on IfcOpenShell. Full native IFC editing, drawing generation, structural analysis, costing/scheduling.
- **IfcOpenShell** — https://github.com/ifcopenshell/ifcopenshell — 2.5k stars, LGPL-3.0, C++/Python IFC library with geometry engine. Supports IFC2x3, IFC4, IFC4x3. Includes IfcConvert CLI, ifcopenshell-python, Bonsai, ifcsverchok, and ifcmcp (MCP server for IFC). v0.8.0 stable, frequent alpha releases through 2026.
- **Bonsai Documentation** — https://docs.bonsaibim.org — Comprehensive tutorials covering IFC model creation, wall/door/window modeling, spatial hierarchy, parametric geometry, material assignment, and Git-based revision tracking.

### Standards
- **IFC (Industry Foundation Classes)** — buildingSMART International standard for BIM data exchange. IFC4x3 is the latest ratified schema.
- **glTF 2.0** — Khronos Group standard for 3D scene interchange, PBR material model (metallic-roughness).
- **Wavefront OBJ/MTL** — Legacy mesh interchange format, limited material support.
