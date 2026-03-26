#!/usr/bin/env python3
"""
generate_floorplan.py
=====================
Reads floorplan-spec.json and produces a 2D floor plan per floor in FreeCAD.
It also generates a 3D model for the floor plan by extruding walls and drawing slabs.

Outputs (per floor):
  output/fcstd/floorplan_F0.FCStd  — FreeCAD project file
  output/dxf/floorplan_F0.dxf     — DXF for architect
  output/svg/freecad_F0.svg       — SVG preview

How to run
----------
Option A — FreeCAD Python console (paste & run):
    exec(open(r'C:/Users/tukum/Downloads/freecad-floorplan/src/generate_floorplan.py').read())

Option B — FreeCAD command line (headless):
    freecadcmd generate_floorplan.py

Option C — FreeCAD GUI menu:
    Macro > Macros... > Execute

Coordinate system
-----------------
  1 unit = 1 mm
  X = plot width  (0 = left,  4000 = right)
  Y = plot depth  (0 = front/street, 25000 = rear)
  Z = 0 (everything flat in the XY plane)
"""

import json
import os
import sys
import math

# ── Locate project files ────────────────────────────────────────────────────
SCRIPT_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in dir()
    else r"C:\Users\tukum\Downloads\freecad-floorplan\src"
)
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir))

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

SPEC_FILE = os.path.join(PROJECT_DIR, "spec", "floorplan-spec.json")
OUT_FCSTD = os.path.join(PROJECT_DIR, "output", "fcstd")
OUT_DXF = os.path.join(PROJECT_DIR, "output", "dxf")
OUT_SVG = os.path.join(PROJECT_DIR, "output", "svg")
OUT_PDF = os.path.join(PROJECT_DIR, "output", "pdf")
OUT_STL = os.path.join(PROJECT_DIR, "output", "stl")
OUT_PNG = os.path.join(PROJECT_DIR, "output", "png")

from floorplan_utils import cumulative_floor_offsets, total_building_height_mm
from facade_utils import floor_elevation_bands, front_facade_features

# ── FreeCAD imports ─────────────────────────────────────────────────────────
try:
    import FreeCAD
    import Draft
    import Part

    try:
        import FreeCADGui
    except ImportError:
        FreeCADGui = None

    print("FreeCAD loaded OK")
except ImportError:
    print("ERROR: FreeCAD modules not found.")
    print("Run this script inside FreeCAD (Python console or Macro menu).")
    sys.exit(1)

# ── Load spec ───────────────────────────────────────────────────────────────
with open(SPEC_FILE, encoding="utf-8") as fh:
    spec = json.load(fh)


def ensure_output_dirs():
    """Create all output folders used by the workflow."""
    for path in (OUT_FCSTD, OUT_DXF, OUT_SVG, OUT_PDF, OUT_STL, OUT_PNG):
        os.makedirs(path, exist_ok=True)


# ── Drawing helpers ──────────────────────────────────────────────────────────


def V(x, y, z=0):
    """Shorthand FreeCAD Vector."""
    return FreeCAD.Vector(x, y, z)


def make_rect(x, y, w, h, label, group, face=True):
    """Filled rectangle (closed wire) from corner (x,y) with size w x h."""
    pts = [V(x, y), V(x + w, y), V(x + w, y + h), V(x, y + h)]
    obj = Draft.makeWire(pts, closed=True, face=face)
    obj.Label = label
    group.addObject(obj)
    return obj


def make_box(x, y, z, w, h, height, label, group):
    """3D Box (extrusion)."""
    obj = doc.addObject("Part::Box", label)
    obj.Length = w
    obj.Width = h
    obj.Height = height
    obj.Placement = FreeCAD.Placement(V(x, y, z), FreeCAD.Rotation())
    group.addObject(obj)
    return obj


def make_line(x1, y1, x2, y2, label, group):
    """Single line segment."""
    obj = Draft.makeLine(V(x1, y1), V(x2, y2))
    obj.Label = label
    group.addObject(obj)
    return obj


def make_text(text, x, y, size_mm, group):
    """Text annotation."""
    obj = Draft.makeText([text], point=V(x, y))
    obj.Label = "txt_" + text[:20].replace(" ", "_")
    if obj.ViewObject:
        obj.ViewObject.FontSize = size_mm
    group.addObject(obj)
    return obj


def make_arc(cx, cy, r, start_deg, end_deg, label, group):
    """Arc for door swings: center, radius, start/end angles in degrees."""
    obj = Draft.makeCircle(
        r,
        placement=FreeCAD.Placement(V(cx, cy), FreeCAD.Rotation()),
        face=False,
        startangle=start_deg,
        endangle=end_deg,
    )
    obj.Label = label
    group.addObject(obj)
    return obj


def make_circle(cx, cy, r, label, group, face=False):
    """Circle (e.g. for drain symbol)."""
    obj = Draft.makeCircle(
        r, placement=FreeCAD.Placement(V(cx, cy), FreeCAD.Rotation()), face=face
    )
    obj.Label = label
    group.addObject(obj)
    return obj


# ── Fill colors for room types ──────────────────────────────────────────────
FILL_COLORS = {
    "parking": (0.91, 0.93, 0.95),
    "commercial": (1.00, 1.00, 1.00),
    "lift_shaft": (0.80, 0.84, 0.88),
    "staircase": (0.91, 0.93, 0.95),
    "core_void": (0.94, 0.97, 1.00),
    "utility": (0.98, 0.98, 0.98),
    "bathroom": (0.86, 0.91, 0.98),
    "rear_void": (0.94, 0.97, 1.00),
    "bedroom": (1.00, 0.98, 0.94),
    "living": (0.98, 1.00, 0.96),
    "kitchen": (1.00, 0.97, 0.92),
    "balcony": (0.92, 0.97, 0.92),
    "terrace": (0.92, 0.97, 0.92),
    "living_room": (0.98, 1.00, 0.96),
    "working_room": (0.91, 0.93, 0.97),
    "master_bedroom": (1.00, 0.98, 0.94),
    "bedroom_2": (1.00, 0.91, 0.82),
    "ensuite": (0.86, 0.91, 0.98),
    "laundry": (0.96, 0.96, 0.96),
    "bedroom": (1.00, 0.95, 0.88),
}


def draw_floor(spec, floor):
    """Draw a single floor and return the FreeCAD document."""
    global doc  # Needed for make_box
    ensure_output_dirs()
    level = floor["level"]
    doc_name = f"Tubehouse_F{level}"
    print(f"\n{'=' * 60}")
    print(f"Processing: {floor['name']} (level {level})")
    print(f"{'=' * 60}")

    # Close existing doc with same name if present
    if doc_name in [d.Name for d in FreeCAD.listDocuments().values()]:
        FreeCAD.closeDocument(doc_name)
    doc = FreeCAD.newDocument(doc_name)

    # ── Layer groups (become DXF layers on export) ───────────────────────────
    grp_2d = doc.addObject("App::DocumentObjectGroup", "2D_PLAN")
    grp_3d = doc.addObject("App::DocumentObjectGroup", "3D_MODEL")

    grp_walls = doc.addObject("App::DocumentObjectGroup", "WALLS")
    grp_rooms = doc.addObject("App::DocumentObjectGroup", "ROOMS")
    grp_stairs = doc.addObject("App::DocumentObjectGroup", "STAIRS")
    grp_symbols = doc.addObject("App::DocumentObjectGroup", "SYMBOLS")
    grp_labels = doc.addObject("App::DocumentObjectGroup", "LABELS")
    grp_dims = doc.addObject("App::DocumentObjectGroup", "DIMENSIONS")

    grp_2d.addObject(grp_walls)
    grp_2d.addObject(grp_rooms)
    grp_2d.addObject(grp_stairs)
    grp_2d.addObject(grp_symbols)
    grp_2d.addObject(grp_labels)
    grp_2d.addObject(grp_dims)

    # ── 1. WALLS (2D & 3D) ───────────────────────────────────────────────────
    print("  Drawing walls...")
    ceiling_height = floor.get("floor_to_ceiling_mm", 3500)
    for wall in floor.get("walls", []):
        # 2D
        obj_2d = make_rect(
            wall["x"],
            wall["y"],
            wall["w"],
            wall["h"],
            wall["label"] + "_2D",
            grp_walls,
            face=True,
        )
        if obj_2d.ViewObject:
            obj_2d.ViewObject.ShapeColor = (0.20, 0.25, 0.33)

        # 3D
        obj_3d = make_box(
            wall["x"],
            wall["y"],
            0,
            wall["w"],
            wall["h"],
            ceiling_height,
            wall["label"] + "_3D",
            grp_3d,
        )
        if obj_3d.ViewObject:
            obj_3d.ViewObject.ShapeColor = (0.90, 0.90, 0.90)

    # ── 2. ROOM FILLS (2D) & SLAB (3D) ───────────────────────────────────────
    print("  Drawing room fills and 3D slab...")
    for room in floor.get("rooms", []):
        obj = make_rect(
            room["x"],
            room["y"],
            room["w"],
            room["h"],
            room["name"],
            grp_rooms,
            face=True,
        )
        color = FILL_COLORS.get(room["id"], (1, 1, 1))
        if obj.ViewObject:
            obj.ViewObject.ShapeColor = color
            obj.ViewObject.Transparency = 30

    # 3D Floor Slab
    plot_w = spec["project"]["plot_width_mm"]
    plot_d = spec["project"]["plot_depth_mm"]
    slab = make_box(0, 0, -200, plot_w, plot_d, 200, "Floor_Slab_3D", grp_3d)
    if slab.ViewObject:
        slab.ViewObject.ShapeColor = (0.7, 0.7, 0.7)

    # ── 3. STAIRS (2D & 3D) ──────────────────────────────────────────────────
    stair = next((e for e in floor.get("elements", []) if e["type"] == "stairs"), None)
    if stair:
        print("  Drawing staircase...")
        sx, sy = stair["x"], stair["y"]
        sw, sh = stair["w"], stair["h"]
        tread = stair["tread_depth_mm"]
        n = stair["num_treads"]
        rise_per_step = ceiling_height / n

        for i in range(1, n + 1):
            ty = sy + i * tread
            if ty < sy + sh:
                # 2D line
                make_line(sx, ty, sx + sw, ty, f"stair_tread_{i:02d}", grp_stairs)

            # 3D step box
            step_3d = make_box(
                sx,
                sy + (i - 1) * tread,
                (i - 1) * rise_per_step,
                sw,
                tread,
                rise_per_step,
                f"stair_step_3D_{i:02d}",
                grp_3d,
            )
            if step_3d.ViewObject:
                step_3d.ViewObject.ShapeColor = (0.6, 0.6, 0.6)

        # UP arrow (2D)
        arrow_x = sx + sw / 2
        make_line(
            arrow_x, sy + sh - 150, arrow_x, sy + 300, "stair_arrow_shaft", grp_stairs
        )
        make_line(
            arrow_x, sy + 300, arrow_x - 120, sy + 600, "stair_arrow_L", grp_stairs
        )
        make_line(
            arrow_x, sy + 300, arrow_x + 120, sy + 600, "stair_arrow_R", grp_stairs
        )

    # ── 4. LIFT ──────────────────────────────────────────────────────────────
    lift = next((e for e in floor.get("elements", []) if e["type"] == "lift"), None)
    if lift:
        print("  Drawing lift shaft...")
        lx, ly, lw, lh = lift["x"], lift["y"], lift["w"], lift["h"]
        make_line(lx, ly, lx + lw, ly + lh, "lift_X1", grp_symbols)
        make_line(lx + lw, ly, lx, ly + lh, "lift_X2", grp_symbols)

    # ── 5. LIGHT WELLS ───────────────────────────────────────────────────────
    for e in floor.get("elements", []):
        if e["type"] == "light_well":
            obj = make_rect(
                e["x"],
                e["y"],
                e["w"],
                e["h"],
                f"void_{e['id']}",
                grp_symbols,
                face=False,
            )
            if obj.ViewObject:
                obj.ViewObject.DrawStyle = "Dashdot"
                obj.ViewObject.LineColor = (0.58, 0.77, 0.99)

    # ── 6. SANITARY FIXTURES ─────────────────────────────────────────────────
    for e in floor.get("elements", []):
        if e["type"] == "toilet":
            print("  Drawing sanitary fixtures...")
            make_rect(
                e["x"],
                e["y"],
                e["tank_w"],
                e["tank_h"],
                f"{e['id']}_cistern",
                grp_symbols,
                face=False,
            )
            bx = e["bowl_cx"] - e["bowl_rx"]
            by = e["bowl_cy"] - e["bowl_ry"]
            make_rect(
                bx,
                by,
                e["bowl_rx"] * 2,
                e["bowl_ry"] * 2,
                f"{e['id']}_bowl",
                grp_symbols,
                face=False,
            )

        elif e["type"] == "sink":
            make_rect(
                e["x"], e["y"], e["w"], e["h"], f"{e['id']}", grp_symbols, face=False
            )
            make_circle(
                e["x"] + e["w"] / 2,
                e["y"] + e["h"] / 2,
                55,
                f"{e['id']}_drain",
                grp_symbols,
            )

    # ── 6b. WINDOWS ───────────────────────────────────────────────────────────
    for e in floor.get("elements", []):
        if e["type"] == "window":
            wx = e["x"]
            wy = e["y"]
            ww = e["width_mm"]
            wt = e.get("wall_thickness_mm", 200)
            mid_y = wy + wt / 2
            # Center line of glass
            make_line(wx, mid_y, wx + ww, mid_y, f"win_{e['id']}_glass", grp_symbols)
            # Perpendicular ticks at edges
            make_line(
                wx, wy + 20, wx, wy + wt - 20, f"win_{e['id']}_tick_L", grp_symbols
            )
            make_line(
                wx + ww,
                wy + 20,
                wx + ww,
                wy + wt - 20,
                f"win_{e['id']}_tick_R",
                grp_symbols,
            )
        elif e["type"] == "pergola":
            obj = make_rect(
                e["x"], e["y"], e["w"], e["h"], e["id"], grp_symbols, face=False
            )
            if obj.ViewObject:
                obj.ViewObject.DrawStyle = "Dashdot"
                obj.ViewObject.LineColor = (0.55, 0.40, 0.24)
            bay = max(int(e["w"] / 6), 1)
            for offset in range(bay, e["w"], bay):
                make_line(
                    e["x"] + offset,
                    e["y"],
                    e["x"] + offset,
                    e["y"] + e["h"],
                    f"{e['id']}_slat_{offset}",
                    grp_symbols,
                )
        elif e["type"] == "planter":
            obj = make_rect(
                e["x"], e["y"], e["w"], e["h"], e["id"], grp_symbols, face=True
            )
            if obj.ViewObject:
                obj.ViewObject.ShapeColor = (0.76, 0.90, 0.76)
                obj.ViewObject.LineColor = (0.27, 0.45, 0.24)
                obj.ViewObject.Transparency = 20
        elif e["type"] == "solar_panels":
            obj = make_rect(
                e["x"], e["y"], e["w"], e["h"], e["id"], grp_symbols, face=False
            )
            if obj.ViewObject:
                obj.ViewObject.LineColor = (0.14, 0.28, 0.50)
            cols = 4
            col_width = e["w"] / cols
            for index in range(1, cols):
                x = e["x"] + index * col_width
                make_line(
                    x, e["y"], x, e["y"] + e["h"], f"{e['id']}_col_{index}", grp_symbols
                )
            make_line(
                e["x"],
                e["y"],
                e["x"] + e["w"],
                e["y"] + e["h"],
                f"{e['id']}_diag_1",
                grp_symbols,
            )
            make_line(
                e["x"] + e["w"],
                e["y"],
                e["x"],
                e["y"] + e["h"],
                f"{e['id']}_diag_2",
                grp_symbols,
            )

    # ── 7. DOORS (data-driven from spec) ─────────────────────────────────────
    print("  Drawing doors...")
    for door in floor.get("doors", []):
        if door["type"] == "swing":
            make_line(
                door["leaf_x1"],
                door["leaf_y1"],
                door["leaf_x2"],
                door["leaf_y2"],
                f"{door['id']}_leaf",
                grp_symbols,
            )
            make_arc(
                door["arc_cx"],
                door["arc_cy"],
                door["arc_r"],
                door["arc_start"],
                door["arc_end"],
                f"{door['id']}_arc",
                grp_symbols,
            )
        elif door["type"] == "sliding":
            # Sliding door: two parallel lines spanning the opening
            sx = door["x"]
            sy = door["y"]
            sw = door["width_mm"]
            wt = door.get("wall_thickness_mm", 100)
            make_line(sx, sy, sx + sw, sy, f"{door['id']}_track1", grp_symbols)
            make_line(
                sx, sy + wt, sx + sw, sy + wt, f"{door['id']}_track2", grp_symbols
            )
        elif door["type"] == "garage_opening":
            obj = make_line(
                door["x"],
                door.get("y", 10),
                door["x"] + door["width_mm"],
                door.get("y", 10),
                door["id"],
                grp_symbols,
            )
            if obj.ViewObject:
                obj.ViewObject.DrawStyle = "Dashed"

    # ── 8. LABELS (data-driven from spec) ────────────────────────────────────
    print("  Adding labels...")
    for lbl in floor.get("labels", []):
        make_text(lbl["text"], lbl["x"], lbl["y"], lbl["size"], grp_labels)

    # ── 9. DIMENSION LINES ───────────────────────────────────────────────────
    print("  Adding dimensions...")
    DIM_OFFSET = 300

    # Total width
    doc_w = Draft.makeDimension(
        V(0, -DIM_OFFSET), V(plot_w, -DIM_OFFSET), V(plot_w / 2, -DIM_OFFSET - 200)
    )
    doc_w.Label = "dim_total_width"
    grp_dims.addObject(doc_w)

    # Total height
    doc_h = Draft.makeDimension(
        V(-DIM_OFFSET, 0), V(-DIM_OFFSET, plot_d), V(-DIM_OFFSET - 200, plot_d / 2)
    )
    doc_h.Label = "dim_total_height"
    grp_dims.addObject(doc_h)

    # Zone height chain (right side)
    zones = floor.get("zones", [])
    if zones:
        zone_y = [z["y_start"] for z in zones] + [zones[-1]["y_end"]]
        for i in range(len(zone_y) - 1):
            d = Draft.makeDimension(
                V(plot_w + 200, zone_y[i]),
                V(plot_w + 200, zone_y[i + 1]),
                V(plot_w + 400, (zone_y[i] + zone_y[i + 1]) / 2),
            )
            d.Label = f"dim_zone_{i}"
            grp_dims.addObject(d)

    # Core zone widths (below core zone, if core zone exists)
    core_zone = next((z for z in zones if z["id"] == "core"), None)
    if core_zone:
        core_x = [200, 1000, 1100, 2700, 2800, 3800]
        core_y = core_zone["y_end"] + 200
        for i in range(len(core_x) - 1):
            d = Draft.makeDimension(
                V(core_x[i], core_y),
                V(core_x[i + 1], core_y),
                V((core_x[i] + core_x[i + 1]) / 2, core_y + 250),
            )
            d.Label = f"dim_core_x_{i}"
            grp_dims.addObject(d)

    # ── 10. SAVE ─────────────────────────────────────────────────────────────
    out_fcstd = os.path.join(OUT_FCSTD, f"floorplan_F{level}.FCStd")
    out_dxf = os.path.join(OUT_DXF, f"floorplan_F{level}.dxf")
    out_svg = os.path.join(OUT_SVG, f"freecad_F{level}.svg")

    print("  Recomputing and saving...")
    doc.recompute()
    doc.saveAs(out_fcstd)
    print(f"    Saved: {out_fcstd}")

    # ── 11. EXPORT DXF ───────────────────────────────────────────────────────
    print("  Exporting DXF...")
    try:
        import importDXF

        export_objects = (
            grp_walls.OutList
            + grp_stairs.OutList
            + grp_symbols.OutList
            + grp_labels.OutList
            + grp_dims.OutList
        )
        importDXF.export(export_objects, out_dxf)
        print(f"    Exported: {out_dxf}")
    except Exception as exc:
        print(f"    DXF auto-export failed: {exc}")
        print("    -> Open FreeCAD, select all objects, File > Export > AutoCAD DXF")

    # ── 12. EXPORT SVG ───────────────────────────────────────────────────────
    try:
        import importSVG

        export_objects = (
            grp_walls.OutList
            + grp_rooms.OutList
            + grp_stairs.OutList
            + grp_symbols.OutList
        )
        importSVG.export(export_objects, out_svg)
        print(f"    SVG exported: {out_svg}")
    except Exception as exc:
        print(f"    SVG export skipped: {exc}")

    print(f"  Floor {level} complete.")
    return doc


def export_svg_to_pdf(svg_path, pdf_path):
    """Convert an SVG file to PDF when cairosvg is installed."""
    if not os.path.isfile(svg_path):
        return False, f"missing SVG input: {svg_path}"
    try:
        import cairosvg

        cairosvg.svg2pdf(url=svg_path, write_to=pdf_path)
        return True, pdf_path
    except Exception as exc:
        return False, str(exc)


def capture_isometric_view(doc_name, out_png):
    """Capture an isometric screenshot when the GUI module is available."""
    if FreeCADGui is None:
        print("  Screenshot skipped: FreeCADGui unavailable in this session.")
        return None
    try:
        FreeCAD.setActiveDocument(doc_name)
        gui_doc = FreeCADGui.getDocument(doc_name)
        if gui_doc is None:
            raise RuntimeError(f"GUI document not available: {doc_name}")
        view = gui_doc.activeView()
        view.viewIsometric()
        view.fitAll()
        view.saveImage(out_png, 1600, 1200, "White")
        print(f"  Screenshot saved: {out_png}")
        return out_png
    except Exception as exc:
        print(f"  Screenshot skipped: {exc}")
        return None


def export_document_stl(doc, out_stl):
    """Export all part solids from a document to STL."""
    try:
        import Mesh

        solids = [
            obj
            for obj in doc.Objects
            if getattr(obj, "TypeId", "").startswith("Part::")
        ]
        if not solids:
            raise RuntimeError("no Part solids found for STL export")
        Mesh.export(solids, out_stl)
        print(f"  STL exported: {out_stl}")
        return out_stl
    except Exception as exc:
        print(f"  STL export skipped: {exc}")
        return None


def draw_front_facade(spec):
    """Draw a simple front facade elevation from the floor plan spec."""
    global doc
    ensure_output_dirs()
    doc_name = "Tubehouse_Front_Facade"
    print(f"\n{'=' * 60}")
    print("Processing: Front Facade Elevation")
    print(f"{'=' * 60}")

    if doc_name in [d.Name for d in FreeCAD.listDocuments().values()]:
        FreeCAD.closeDocument(doc_name)
    doc = FreeCAD.newDocument(doc_name)

    grp_elevation = doc.addObject("App::DocumentObjectGroup", "ELEVATION")
    grp_openings = doc.addObject("App::DocumentObjectGroup", "OPENINGS")
    grp_labels = doc.addObject("App::DocumentObjectGroup", "LABELS")
    grp_dims = doc.addObject("App::DocumentObjectGroup", "DIMENSIONS")

    plot_w = spec["project"]["plot_width_mm"]
    bands = floor_elevation_bands(spec["floors"])
    floor_lookup = {floor["level"]: floor for floor in spec["floors"]}

    for band in bands:
        base_z = band["base_z_mm"]
        height = band["height_mm"]
        level = band["level"]

        outline = make_rect(
            0,
            base_z,
            plot_w,
            height,
            f"F{level}_facade_outline",
            grp_elevation,
            face=False,
        )
        if outline.ViewObject:
            outline.ViewObject.LineWidth = 2.0
            outline.ViewObject.LineColor = (0.20, 0.25, 0.33)
        make_line(0, base_z, plot_w, base_z, f"F{level}_slab_line", grp_elevation)
        make_text(f"F{level}", -550, base_z + height / 2, 180, grp_labels)

        facade = front_facade_features(floor_lookup[level])
        if facade["has_front_balcony"]:
            rail = make_rect(
                200,
                base_z + 950,
                plot_w - 400,
                1050,
                f"F{level}_balcony_rail",
                grp_openings,
                face=False,
            )
            if rail.ViewObject:
                rail.ViewObject.LineColor = (0.10, 0.45, 0.35)
            make_line(
                200,
                base_z + 1500,
                plot_w - 200,
                base_z + 1500,
                f"F{level}_balcony_midrail",
                grp_openings,
            )

        for opening in facade["openings"]:
            opening_obj = make_rect(
                opening["x"],
                base_z + opening["sill_mm"],
                opening["width_mm"],
                opening["height_mm"],
                opening["id"],
                grp_openings,
                face=False,
            )
            if opening_obj.ViewObject:
                if opening["kind"] == "garage_opening":
                    opening_obj.ViewObject.LineColor = (0.25, 0.25, 0.25)
                    opening_obj.ViewObject.LineWidth = 2.0
                elif opening["kind"] == "glazing":
                    opening_obj.ViewObject.LineColor = (0.24, 0.50, 0.76)
                else:
                    opening_obj.ViewObject.LineColor = (0.35, 0.35, 0.35)

        make_text(
            band["name"].upper(), plot_w / 2, base_z + height - 350, 130, grp_labels
        )

    total_height_mm = bands[-1]["top_z_mm"] if bands else 0
    roof_line = make_line(
        0, total_height_mm, plot_w, total_height_mm, "roof_line", grp_elevation
    )
    if roof_line.ViewObject:
        roof_line.ViewObject.LineWidth = 2.0

    total_dim = Draft.makeDimension(
        V(plot_w + 500, 0),
        V(plot_w + 500, total_height_mm),
        V(plot_w + 900, total_height_mm / 2),
    )
    total_dim.Label = "facade_total_height"
    grp_dims.addObject(total_dim)

    for band in bands:
        dim = Draft.makeDimension(
            V(plot_w + 150, band["base_z_mm"]),
            V(plot_w + 150, band["top_z_mm"]),
            V(plot_w + 350, (band["base_z_mm"] + band["top_z_mm"]) / 2),
        )
        dim.Label = f"facade_floor_{band['level']}_height"
        grp_dims.addObject(dim)

    out_fcstd = os.path.join(OUT_FCSTD, "front_facade_elevation.FCStd")
    out_dxf = os.path.join(OUT_DXF, "front_facade_elevation.dxf")
    out_svg = os.path.join(OUT_SVG, "front_facade_elevation.svg")

    doc.recompute()
    doc.saveAs(out_fcstd)
    print(f"  Saved: {out_fcstd}")

    try:
        import importDXF

        importDXF.export(
            grp_elevation.OutList
            + grp_openings.OutList
            + grp_labels.OutList
            + grp_dims.OutList,
            out_dxf,
        )
        print(f"  DXF exported: {out_dxf}")
    except Exception as exc:
        print(f"  Facade DXF export skipped: {exc}")

    try:
        import importSVG

        importSVG.export(
            grp_elevation.OutList + grp_openings.OutList + grp_labels.OutList, out_svg
        )
        print(f"  SVG exported: {out_svg}")
    except Exception as exc:
        print(f"  Facade SVG export skipped: {exc}")

    return doc


# ── 3D stacking: combine all floors in one document ─────────────────────────


def stack_floors(floor_specs, floor_height=3.2, regenerate_individual=True):
    """Stack floors F0→F4 into a single FreeCAD 3D document.

    Calls the per-floor generation function for each floor to produce the
    individual .FCStd outputs, then assembles a combined document where each
    floor's geometry is offset vertically by ``floor_index × floor_height``
    metres (converted to mm internally).

    Parameters
    ----------
    floor_specs : list
        List of floor spec dicts taken directly from ``spec["floors"]``.
    floor_height : float
        Nominal storey height in **metres** (default 3.2 m → 3200 mm).
        Each floor is offset by ``level × floor_height × 1000`` mm in Z.

    Returns
    -------
    FreeCAD.Document
        The combined document (also saved to output/fcstd/tubehouse_full_3d.FCStd).
    """
    global doc  # make_box uses the global doc reference
    ensure_output_dirs()
    z_offsets = cumulative_floor_offsets(floor_specs, floor_height)

    # ── Step 1: generate individual per-floor documents ──────────────────────
    print("\n" + "=" * 60)
    print("stack_floors: generating per-floor documents ...")
    print("=" * 60)
    if regenerate_individual:
        for floor in floor_specs:
            draw_floor(spec, floor)

    # ── Step 2: create the combined document ─────────────────────────────────
    combined_name = "Tubehouse_Full_3D"
    if combined_name in [d.Name for d in FreeCAD.listDocuments().values()]:
        FreeCAD.closeDocument(combined_name)
    combined_doc = FreeCAD.newDocument(combined_name)
    grp_all = combined_doc.addObject("App::DocumentObjectGroup", "ALL_FLOORS")

    # ── Step 3: re-create 3D geometry for each floor at the correct Z ────────
    doc = combined_doc  # redirect make_box to the combined document
    plot_w = spec["project"]["plot_width_mm"]
    plot_d = spec["project"]["plot_depth_mm"]

    for floor in floor_specs:
        level = floor["level"]
        z_offset = z_offsets[level]
        ceiling_h = floor.get("floor_to_ceiling_mm", int(floor_height * 1000))

        print(f"\n  Stacking F{level} — '{floor['name']}' at Z={z_offset} mm")

        grp_floor = combined_doc.addObject("App::DocumentObjectGroup", f"Floor_{level}")
        grp_all.addObject(grp_floor)

        # 3D walls
        for wall in floor.get("walls", []):
            obj = make_box(
                wall["x"],
                wall["y"],
                z_offset,
                wall["w"],
                wall["h"],
                ceiling_h,
                f"F{level}_{wall['id']}_3D",
                grp_floor,
            )
            if obj.ViewObject:
                obj.ViewObject.ShapeColor = (0.90, 0.90, 0.90)

        # 3D floor slab (200 mm thick, sits just below z_offset)
        slab = make_box(
            0,
            0,
            z_offset - 200,
            plot_w,
            plot_d,
            200,
            f"F{level}_Slab_3D",
            grp_floor,
        )
        if slab.ViewObject:
            slab.ViewObject.ShapeColor = (0.70, 0.70, 0.70)

    # ── Step 4: save combined document ───────────────────────────────────────
    combined_doc.recompute()
    out_fcstd = os.path.join(OUT_FCSTD, "tubehouse_full_3d.FCStd")
    combined_doc.saveAs(out_fcstd)
    print(f"\n  Saved combined 3D: {out_fcstd}")

    # ── Step 5: export combined DXF ──────────────────────────────────────────
    out_dxf = os.path.join(OUT_DXF, "tubehouse_full_3d.dxf")
    try:
        import importDXF

        importDXF.export(grp_all.OutList, out_dxf)
        print(f"  DXF exported:     {out_dxf}")
    except Exception as exc:
        print(f"  DXF export skipped: {exc}")

    capture_isometric_view(
        combined_name,
        os.path.join(OUT_PNG, "tubehouse_full_3d_isometric.png"),
    )

    total_h_mm = total_building_height_mm(floor_specs, floor_height)
    print(
        f"\nstack_floors complete — {len(floor_specs)} floors, "
        f"total height {total_h_mm / 1000:.1f} m"
    )
    return combined_doc


def export_architect_package(stacked_doc=None):
    """Export best-effort package artifacts for architect handoff."""
    ensure_output_dirs()
    print(f"\n{'=' * 60}")
    print("Exporting architect package")
    print(f"{'=' * 60}")
    manifest = {"generated": [], "skipped": []}

    for floor in spec["floors"]:
        level = floor["level"]
        svg_path = os.path.join(OUT_SVG, f"freecad_F{level}.svg")
        pdf_path = os.path.join(OUT_PDF, f"floorplan_F{level}.pdf")
        ok, detail = export_svg_to_pdf(svg_path, pdf_path)
        if ok:
            manifest["generated"].append(pdf_path)
            print(f"  PDF exported: {pdf_path}")
        else:
            manifest["skipped"].append({"target": pdf_path, "reason": detail})
            print(f"  PDF skipped: {pdf_path} ({detail})")

    facade_svg = os.path.join(OUT_SVG, "front_facade_elevation.svg")
    facade_pdf = os.path.join(OUT_PDF, "front_facade_elevation.pdf")
    ok, detail = export_svg_to_pdf(facade_svg, facade_pdf)
    if ok:
        manifest["generated"].append(facade_pdf)
        print(f"  PDF exported: {facade_pdf}")
    else:
        manifest["skipped"].append({"target": facade_pdf, "reason": detail})
        print(f"  PDF skipped: {facade_pdf} ({detail})")

    if stacked_doc is not None:
        out_stl = os.path.join(OUT_STL, "tubehouse_full_3d.stl")
        stl_path = export_document_stl(stacked_doc, out_stl)
        if stl_path:
            manifest["generated"].append(stl_path)
        else:
            manifest["skipped"].append(
                {"target": out_stl, "reason": "STL export failed"}
            )

    screenshot = os.path.join(OUT_PNG, "tubehouse_full_3d_isometric.png")
    if os.path.isfile(screenshot):
        manifest["generated"].append(screenshot)
    else:
        manifest["skipped"].append(
            {"target": screenshot, "reason": "screenshot not available"}
        )

    manifest_path = os.path.join(
        PROJECT_DIR, "output", "architect_package_manifest.json"
    )
    with open(manifest_path, "w", encoding="utf-8") as handle:
        json.dump(manifest, handle, indent=2)
    print(f"  Manifest saved: {manifest_path}")
    return manifest


def generate_all_floors():
    """Generate individual floor outputs for every floor in the spec."""
    for floor in spec["floors"]:
        draw_floor(spec, floor)
    print(f"\nDone - processed {len(spec['floors'])} floor(s).")


def env_flag(name):
    """Parse a truthy environment flag."""
    return os.environ.get(name, "0").strip().lower() in {"1", "true", "yes", "on"}


def main():
    """Entry point for batch generation inside FreeCAD."""
    ensure_output_dirs()
    generate_all_floors()

    stacked_doc = None
    if env_flag("GENERATE_STACKED"):
        stacked_doc = stack_floors(spec["floors"], regenerate_individual=False)
    if env_flag("GENERATE_FACADE"):
        draw_front_facade(spec)
    if env_flag("EXPORT_ARCHITECT_PACKAGE"):
        export_architect_package(stacked_doc=stacked_doc)

    print("To generate the full 3D stacked model manually, call:")
    print("  stack_floors(spec['floors'])")
    print("To draw the front facade manually, call:")
    print("  draw_front_facade(spec)")
    print("To export the architect package manually, call:")
    print("  export_architect_package(stacked_doc=None)")


# ── Main entrypoint ─────────────────────────────────────────────────────────
if __name__ == "__main__":
    main()
