# Research Brief: FreeCAD-Blender Floorplan-to-3D Workflow

**Date:** 2026-05-11
**Modes run:** domain, codebase
**Depth:** standard
**Invocation context:** Research FreeCAD Blender workflow for floorplan to 3D design

---

## Synthesis

The FreeCAD-to-Blender floorplan-to-3D pipeline has mature tooling at every layer, but the dominant pattern in 2025-2026 is shifting from direct mesh interchange (OBJ/FBX) toward IFC-based BIM interoperability. Our codebase currently uses the simpler OBJ approach, which works but sacrifices semantic richness — no wall opening subtraction, no door/window 3D geometry, no material properties beyond diffuse color. The most impactful upgrade path is to adopt FreeCAD's Arch workbench (`Arch.makeWall`, `Arch.makeWindowPreset`) for geometry generation, then export IFC via IfcOpenShell's Python API. This unlocks BlenderBIM/Bonsai for native IFC authoring in Blender and provides a structured BIM dataset that any AEC tool can consume. In the shorter term, adding glTF as a second export format and improving OBJ mesh quality (normals, filtering 2D objects) would yield immediate visual improvements in Blender renders without requiring an architectural refactor of the generator.

The codebase is well-structured for incremental improvement: `floorplan-spec.json` is the clean single source of truth, `floorplan_utils.py` and `facade_utils.py` contain pure testable logic, and the Blender scripts already support a JSON sidecar for material overrides. The key gap is that `generate_floorplan.py` uses raw `Part::Box` primitives instead of FreeCAD's Arch/BIM workbench, which means 3D window and door geometry is absent and IFC export is impossible without upstream changes.

## Domain

### Discovery

**FreeCAD Arch/BIM Workbench**: FreeCAD's built-in architectural modeling tools, including `Arch.makeWall()`, `Arch.makeWindowPreset()`, `Arch.makeStructure()`, `Arch.makeFloor()`, and `Arch.makeBuilding()`. These create parametric BIM objects with proper IfcClassification, material associations, and automatic opening subtraction in walls ([FreeCAD Wiki — Arch Workbench](https://wiki.freecad.org/Arch_Workbench), verified via IfcOpenShell docs cross-references).

**IfcOpenShell / Bonsai** (formerly BlenderBIM): An open-source IFC library (2.5k GitHub stars, LGPL-3.0) with a Python API for creating, querying, and modifying IFC files. Bonsai (v0.8.x) is the Blender add-on providing native IFC authoring inside Blender. IfcOpenShell's `ifcopenshell.api` module supports creating walls, doors, windows, storeys, and sites programmatically ([GitHub — IfcOpenShell/IfcOpenShell](https://github.com/IfcOpenShell/IfcOpenShell)).

**Blender Architectural Add-ons**:
- **Archimesh** (bundled with Blender): Creates rooms, cabinets, stairs, columns — targeted at interior viz, not BIM
- **Archipack** (bundled with Blender): Parametric doors, windows, floors, walls — good for visualization but no IFC support
- **Bonsai** (formerly BlenderBIM): Native IFC authoring in Blender; opens/saves IFC directly, rounds trips with FreeCAD

**Format Landscape (2025-2026)**:

| Format | Geometry | Materials | Semantics | BIM Support | Our Use |
|---------|----------|-----------|-----------|-------------|---------|
| OBJ | Mesh only | MTL (basic Kd/Ks/Ns) | None | None | Current |
| FBX | Mesh + armature | PBR-capable | Limited | None | Not used |
| glTF 2.0 | Mesh + PBR | Full PBR (metallic-roughness) | Extensions | glTF-BIM draft | Potential |
| IFC (IFC4) | BREP + mesh | IfcMaterial + IfcMaterialLayerSet | Full (IfcWall, IfcDoor, etc.) | Native BIM | Target |
| STL | Mesh only | None | None | None | Fallback |

### Verification

- IfcOpenShell v0.8.0 released with full IFC4 Add2 TC1 support, active development ([GitHub release history](https://github.com/IfcOpenShell/IfcOpenShell/releases), verified 2026-05-11)
- FreeCAD 1.0 includes NativeIFC workbench built on IfcOpenShell ([FreeCAD changelog](https://wiki.freecad.org/Release_notes_1.0), verified)
- Bonsai (formerly BlenderBIM) v0.8.5+ supports IFC4 native authoring in Blender ([bonsaibim.org](https://bonsaibim.org), verified)
- Blender 4.x moved OBJ import to `bpy.ops.wm.obj_import` and STL import to `bpy.ops.wm.stl_import` ([Blender 4.0 release notes](https://www.blender.org/download/releases/4-0/), verified during our E2E session)

### Comparison

**Direct Mesh Interchange (OBJ/FBX/glTF)**: Simple, universal, no BIM semantics. Good for visualization-only workflows. OBJ loses PBR data. FBX preserves more but is proprietary-format-dependent. glTF is the best mesh-only option with full PBR and broad viewer support.

**IFC via IfcOpenShell**: The gold standard for AEC interoperability. Walls have layers, doors have swing directions, materials have thermal properties. Enables round-trip editing between FreeCAD and Blender. Requires learning the IfcOpenShell API and migrating geometry generation to Arch objects.

**Hybrid (current + IFC)**: The most practical path: keep OBJ for fast visualization, add IFC as a parallel export for BIM consumers. The `floorplan-spec.json` schema already has enough data (wall thicknesses, door positions, room names) to drive both exports from the same source.

### Synthesis

The ecosystem supports three paths: (1) stay OBJ-only and improve mesh quality, (2) add IFC as a parallel export using IfcOpenShell Python API directly from spec JSON without needing FreeCAD Arch objects, or (3) migrate FreeCAD generation to Arch/BIM workbench objects and get IFC for free. Path (2) is the best ROI — it doesn't require restructuring the FreeCAD generator and can be tested independently. Path (3) is the long-term goal for proper BIM round-tripping.

### Confidence
**High**. IFC interoperability via IfcOpenShell/Bonsai is well-documented, actively maintained, and widely adopted in the AEC open-source community.

## Codebase

### Discovery

The repository at `C:\Users\tukum\Downloads\freecad-blender` contains:

- `spec/floorplan-spec.json` (3108 lines) — comprehensive spec with walls, rooms, doors, staircases, light wells, balconies, planters, windows, solar panels across 5 floors
- `src/generate_floorplan.py` (1007 lines) — FreeCAD geometry generator using `Part::Box` and `Draft.makeRectangle`/`Draft.makeDimension`
- `src/floorplan_utils.py` — Pure Python helpers for floor height calculations
- `src/facade_utils.py` — Pure Python helpers for facade feature extraction
- `src/blender_export_utils.py` — Per-floor and combined OBJ/MTL export with named groups
- `src/blender_materials.py` (191 lines) — 10 PBR materials, convention-based + JSON sidecar assignment
- `src/setup_blender_scene.py` (296 lines) — Scene assembly: OBJ import, material assignment, sun/fill lights, camera
- `src/render_blender.py` (117 lines) — Headless Cycles render, configurable samples/resolution
- `spec/blender_materials.json` — Data-driven material/lighting/camera/render config

### Verification

Key architectural observations verified by reading the source:

1. **No Arch/BIM objects**: `generate_floorplan.py` uses `Part.makeBox()` for walls and slabs. No `Arch.makeWall()` or `Arch.makeWindowPreset()` calls exist in the codebase ([confirmed via grep](src/generate_floorplan.py)).

2. **OBJ groups by convention**: `blender_export_utils.py` creates named groups like `F0_wall_exterior` and `F0_room_living` which `setup_blender_scene.py` maps to materials via string matching. This is fragile but functional.

3. **2D geometry pollution**: `Draft.makeRectangle`, `Draft.makeDimension`, `Draft.makeText` create 2D annotation objects that get exported in OBJ alongside 3D solids. The Blender setup script filters by object type (`MESH`), but the OBJ file itself contains these 2D shapes.

4. **JSON sidecar is extensible**: `spec/blender_materials.json` already supports room/zone/obj_group material overrides, HDRI backgrounds, and custom camera positions — ready for glTF material extensions.

5. **Pure Python modules are testable**: `floorplan_utils.py`, `facade_utils.py`, `blender_export_utils.py`, and `blender_materials.py` all have `unittest` test suites (35 tests total) that run without FreeCAD or Blender.

### Comparison

**Current architecture (OBJ-centric)**:
```
floorplan-spec.json → FreeCAD (Part::Box) → OBJ/MTL → Blender → Cycles PNG
```

**Proposed IFC-augmented architecture**:
```
floorplan-spec.json → FreeCAD (Part::Box) → OBJ/MTL → Blender → Cycles PNG
                          ↓ (parallel)
                   IfcOpenShell API → IFC4 → Bonsai/BlenderBIM or any BIM tool
```

**Proposed Arch-migrated architecture (long-term)**:
```
floorplan-spec.json → FreeCAD (Arch.makeWall, Arch.makeWindow) → FCStd + IFC + OBJ → Blender
```

### Synthesis

The codebase is well-factored for incremental extension. The JSON spec is rich enough to drive both OBJ and IFC generation. The minimal-change path is to add an `ifc_export_utils.py` that reads `floorplan-spec.json` and generates IFC4 using IfcOpenShell's Python API — completely independent of FreeCAD's geometry pipeline. This would produce semantically rich BIM files without modifying the existing OBJ workflow.

### Confidence
**High**. The codebase analysis is first-hand, based on direct file reads.

## Sources

- [IfcOpenShell GitHub](https://github.com/IfcOpenShell/IfcOpenShell) — open-source IFC library (LGPL-3.0, 2.5k stars, v0.8.0+)
- [IfcOpenShell Python API Documentation](https://docs.ifcopenshell.org/ifcopenshell-python.html) — IfcProject/IfcSite/IfcBuilding/IfcWall creation
- [Bonsai (formerly BlenderBIM)](https://bonsaibim.org) — native IFC authoring in Blender
- [FreeCAD Arch Workbench](https://wiki.freecad.org/Arch_Workbench) — BIM object creation in FreeCAD
- [FreeCAD BIM Workbench](https://wiki.freecad.org/BIM_Workbench) — modern BIM tools integrated into FreeCAD
- [Blender 4.0 Release Notes](https://www.blender.org/download/releases/4-0/) — OBJ/STL API changes
- [IfcOpenShell Python Code Examples](https://github.com/IfcOpenShell/ifcopenshell/blob/v0.8.0/src/ifcopenshell-python/docs/ifcopenshell-python/code_examples.md) — wall/storey creation patterns
- [glTF 2.0 Specification](https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html) — PBR material model
- Local codebase: `src/generate_floorplan.py`, `src/blender_export_utils.py`, `src/blender_materials.py`, `src/setup_blender_scene.py`, `src/render_blender.py`, `spec/floorplan-spec.json`, `spec/blender_materials.json`