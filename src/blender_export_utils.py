"""OBJ export utilities for Blender integration.

Produces per-floor and combined Wavefront OBJ files from FreeCAD
documents, preserving object group names so Blender can assign
materials by convention.
"""

import os
import math

try:
    import FreeCAD
    import Mesh
except ImportError:
    FreeCAD = None
    Mesh = None


OBJ_GROUP_CONVENTIONS = {
    "WALLS": "wall",
    "ROOMS": "room",
    "STAIRS": "stair",
    "SYMBOLS": "symbol",
    "3D_MODEL": "solid",
}

MATERIAL_PALETTE = {
    "wall": {"Kd": (0.80, 0.80, 0.80), "name": "Concrete_Wall"},
    "room": {"Kd": (0.95, 0.95, 0.95), "name": "Room_Fill"},
    "stair": {"Kd": (0.60, 0.60, 0.60), "name": "Stair_Concrete"},
    "symbol": {"Kd": (0.90, 0.90, 0.90), "name": "Symbol_Line"},
    "solid": {"Kd": (0.85, 0.85, 0.85), "name": "Solid_Generic"},
    "slab": {"Kd": (0.70, 0.70, 0.70), "name": "Floor_Slab"},
}


def obj_group_name(floor_level, group_key):
    """Return an OBJ group name like 'F0_Walls' for Blender material assignment."""
    convention = OBJ_GROUP_CONVENTIONS.get(group_key, group_key.lower())
    return f"F{floor_level}_{convention}"


def obj_path_for_floor(output_dir, level):
    """Return the OBJ file path for a given floor level."""
    return os.path.join(output_dir, f"floorplan_F{level}.obj")


def obj_path_for_combined(output_dir):
    """Return the combined OBJ file path for the stacked model."""
    return os.path.join(output_dir, "tubehouse_full_3d.obj")


def write_mtl(mtl_path, palette=None):
    """Write a minimal MTL file with named materials from the palette."""
    if palette is None:
        palette = MATERIAL_PALETTE
    lines = ["# Tubehouse material library\n"]
    for mat_key, mat in palette.items():
        kd = mat["Kd"]
        lines.append(f"newmtl {mat['name']}\n")
        lines.append(f"Ns 10.0\n")
        lines.append(f"Ka {kd[0]:.4f} {kd[1]:.4f} {kd[2]:.4f}\n")
        lines.append(f"Kd {kd[0]:.4f} {kd[1]:.4f} {kd[2]:.4f}\n")
        lines.append(f"Ks 0.1 0.1 0.1\n")
        lines.append(f"d 1.0\n")
        lines.append(f"illum 2\n\n")
    with open(mtl_path, "w", encoding="utf-8") as fh:
        fh.writelines(lines)
    return mtl_path


def _triangulate_mesh(shape):
    """Return a list of (vertices, faces) tuples from a FreeCAD Part shape.

    Each element in the list is (verts, faces) where:
      - verts is a list of (x, y, z) tuples
      - faces is a list of (i0, i1, i2) tuples (0-indexed)
    """
    meshed = Mesh.Mesh(shape)
    result = []
    for sub in meshed.Mesh.subShapes if hasattr(meshed.Mesh, 'subShapes') else [meshed.Mesh]:
        pass
    verts = []
    faces = []
    vert_map = {}
    for i in range(meshed.CountPoints):
        pt = meshed.GetPoint(i)
        verts.append((pt.x, pt.y, pt.z))
    for i in range(meshed.CountFacets):
        face = meshed.GetFace(i)
        faces.append((face.Point1, face.Point2, face.Point3))
    return verts, faces


def _is_3d_solid(obj):
    """Return True if the object has 3D solid geometry worth exporting."""
    if not hasattr(obj, "Shape") or obj.Shape is None:
        return False
    if obj.Shape.Solids:
        return True
    if obj.Shape.Volume > 0:
        return True
    return False


def _compute_face_normals(verts, faces):
    """Compute per-face normals from vertex positions.

    Returns a list of (nx, ny, nz) tuples, one per face.
    Each normal is unit-length and consistently oriented.
    """
    normals = []
    for i0, i1, i2 in faces:
        v0 = verts[i0]
        v1 = verts[i1]
        v2 = verts[i2]
        e1 = (v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2])
        e2 = (v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2])
        nx = e1[1] * e2[2] - e1[2] * e2[1]
        ny = e1[2] * e2[0] - e1[0] * e2[2]
        nz = e1[0] * e2[1] - e1[1] * e2[0]
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        if length > 1e-12:
            nx /= length
            ny /= length
            nz /= length
        else:
            nx, ny, nz = 0.0, 0.0, 1.0
        normals.append((nx, ny, nz))
    return normals


def _export_objects_to_obj(objects, obj_path, mtl_filename, group_prefix="",
                           filter_3d_only=True, scale_factor=0.001):
    """Export a list of FreeCAD objects to an OBJ file.

    Parameters
    ----------
    objects : list
        FreeCAD document objects to export.
    obj_path : str
        Output .obj file path.
    mtl_filename : str
        MTL filename referenced in the OBJ (e.g. 'tubehouse.mtl').
    group_prefix : str
        Prefix for OBJ groups (e.g. 'F0_' for floor 0 objects).
    filter_3d_only : bool
        If True, skip objects without 3D solid geometry (2D wires, dimensions, text).
    scale_factor : float
        Multiply vertex coordinates by this factor. Default 0.001 converts mm to meters.
    """
    vertex_offset = 1
    normal_offset = 1
    units_label = "meters" if scale_factor == 0.001 else "custom"
    obj_lines = [f"# Tubehouse OBJ export\n", f"# units: {units_label}\n",
                 f"mtllib {mtl_filename}\n"]
    current_material = ""

    for obj in objects:
        if not hasattr(obj, "Shape") or obj.Shape is None:
            continue
        if filter_3d_only and not _is_3d_solid(obj):
            continue

        group_name = f"{group_prefix}{obj.Label}".replace(" ", "_")
        material_key = _infer_material_key(obj, group_prefix)
        material_name = MATERIAL_PALETTE.get(material_key, MATERIAL_PALETTE["wall"])["name"]

        obj_lines.append(f"g {group_name}\n")
        if material_name != current_material:
            obj_lines.append(f"usemtl {material_name}\n")
            current_material = material_name

        try:
            mesh_obj = Mesh.Mesh(obj.Shape)
        except Exception:
            continue

        verts = []
        n_verts = mesh_obj.CountPoints
        for i in range(n_verts):
            pt = mesh_obj.GetPoint(i)
            verts.append((pt.x * scale_factor, pt.y * scale_factor, pt.z * scale_factor))
            obj_lines.append(f"v {verts[-1][0]:.6f} {verts[-1][1]:.6f} {verts[-1][2]:.6f}\n")

        faces = []
        for i in range(mesh_obj.CountFacets):
            fc = mesh_obj.GetFace(i)
            faces.append((fc.Point1, fc.Point2, fc.Point3))

        normals = _compute_face_normals(verts, faces)
        for nx, ny, nz in normals:
            obj_lines.append(f"vn {nx:.6f} {ny:.6f} {nz:.6f}\n")

        for fi, (i0, i1, i2) in enumerate(faces):
            ni = fi + normal_offset
            obj_lines.append(
                f"f {i0 + vertex_offset}//{ni} "
                f"{i1 + vertex_offset}//{ni} "
                f"{i2 + vertex_offset}//{ni}\n"
            )

        vertex_offset += n_verts
        normal_offset += len(faces)

    with open(obj_path, "w", encoding="utf-8") as fh:
        fh.writelines(obj_lines)
    return obj_path


def _infer_material_key(obj, group_prefix=""):
    """Infer the material key from an object label or group prefix."""
    label_lower = obj.Label.lower()
    if any(kw in label_lower for kw in ("wall", "ext_", "int_")):
        return "wall"
    if any(kw in label_lower for kw in ("slab", "floor_slab")):
        return "slab"
    if any(kw in label_lower for kw in ("stair", "step")):
        return "stair"
    if any(kw in label_lower for kw in ("symbol", "txt_", "dim_")):
        return "symbol"
    if "3d" in label_lower:
        return "solid"
    return "room"


def export_floor_obj(doc, level, output_dir, filter_3d_only=True, scale_factor=0.001):
    """Export one floor's document objects to OBJ with named groups.

    Parameters
    ----------
    doc : FreeCAD.Document
        The document for the floor.
    level : int
        Floor level (e.g. 0 for ground).
    output_dir : str
        Directory to write .obj and .mtl files.
    filter_3d_only : bool
        If True, skip 2D-only objects (wires, dimensions, text).
    scale_factor : float
        Vertex scale factor. Default 0.001 converts mm to meters.

    Returns
    -------
    str
        Path to the written OBJ file, or None if export failed.
    """
    if FreeCAD is None or Mesh is None:
        print(f"  OBJ export for F{level} skipped: FreeCAD/Mesh not available")
        return None

    os.makedirs(output_dir, exist_ok=True)
    obj_path = obj_path_for_floor(output_dir, level)
    mtl_filename = os.path.basename(obj_path).replace(".obj", ".mtl")
    mtl_path = os.path.join(output_dir, mtl_filename)

    write_mtl(mtl_path)

    group_prefix = f"F{level}_"
    exportable = [
        obj for obj in doc.Objects
        if hasattr(obj, "Shape") and obj.Shape is not None
        and (obj.Shape.Solids or obj.Shape.Wires or obj.Shape.Edges)
    ]

    if not exportable:
        print(f"  OBJ export for F{level}: no exportable objects found, skipping")
        return None

    _export_objects_to_obj(exportable, obj_path, mtl_filename,
                           group_prefix=group_prefix,
                           filter_3d_only=filter_3d_only,
                           scale_factor=scale_factor)
    print(f"  OBJ exported: {obj_path}")
    return obj_path


def export_combined_obj(stacked_doc, output_dir, filter_3d_only=True, scale_factor=0.001):
    """Export the combined stacked model to OBJ with per-floor named groups.

    Parameters
    ----------
    stacked_doc : FreeCAD.Document
        The combined stacked model document.
    output_dir : str
        Directory to write .obj and .mtl files.
    filter_3d_only : bool
        If True, skip 2D-only objects (wires, dimensions, text).
    scale_factor : float
        Vertex scale factor. Default 0.001 converts mm to meters.

    Returns
    -------
    str
        Path to the written OBJ file, or None if export failed.
    """
    if FreeCAD is None or Mesh is None:
        print("  Combined OBJ export skipped: FreeCAD/Mesh not available")
        return None

    os.makedirs(output_dir, exist_ok=True)
    obj_path = obj_path_for_combined(output_dir)
    mtl_path = os.path.join(output_dir, "tubehouse.mtl")

    write_mtl(mtl_path)

    exportable = [
        obj for obj in stacked_doc.Objects
        if hasattr(obj, "Shape") and obj.Shape is not None
        and (obj.Shape.Solids or obj.Shape.Wires or obj.Shape.Edges)
    ]

    if not exportable:
        print("  Combined OBJ export: no exportable objects found, skipping")
        return None

    _export_objects_to_obj(exportable, obj_path, "tubehouse.mtl", group_prefix="",
                           filter_3d_only=filter_3d_only,
                           scale_factor=scale_factor)
    print(f"  Combined OBJ exported: {obj_path}")
    return obj_path