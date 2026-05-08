#!/usr/bin/env python3
"""
setup_blender_scene.py
======================
Imports the combined OBJ tubehouse model into Blender, applies
data-driven materials, adds architectural lighting and a camera,
and saves the result as a .blend file.

Usage
-----
  blender --background --python src/setup_blender_scene.py

Configuration is read from spec/blender_materials.json.
"""

import json
import math
import os
import sys

SCRIPT_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in dir()
    else os.path.dirname(os.path.abspath(sys.argv[0]))
)
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir))

SPEC_FILE = os.path.join(PROJECT_DIR, "spec", "blender_materials.json")
OUT_DIR = os.path.join(PROJECT_DIR, "output", "blend")
OBJ_COMBINED = os.path.join(PROJECT_DIR, "output", "obj", "tubehouse_full_3d.obj")
STL_FALLBACK = os.path.join(PROJECT_DIR, "output", "stl", "tubehouse_full_3d.stl")

if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from blender_materials import (
    MATERIAL_DEFINITIONS,
    OBJ_GROUP_MATERIAL_MAP,
    ROOM_MATERIAL_MAP,
    create_all_materials,
    material_name_for_obj_group,
)

try:
    import bpy
    from mathutils import Vector
except ImportError:
    bpy = None
    Vector = None


def load_config():
    """Load the Blender material config from the JSON sidecar."""
    if not os.path.isfile(SPEC_FILE):
        print(f"  Config not found: {SPEC_FILE}, using defaults from blender_materials.py")
        return None
    with open(SPEC_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def clear_scene():
    """Remove all objects from the current Blender scene."""
    if bpy is None:
        return
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=True)

    for block in bpy.data.meshes:
        if block.users == 0:
            bpy.data.meshes.remove(block)
    for block in bpy.data.materials:
        if block.users == 0:
            bpy.data.materials.remove(block)


def import_obj(obj_path):
    """Import a Wavefront OBJ file. Returns True on success."""
    if bpy is None:
        print("  ERROR: bpy not available, cannot import OBJ.")
        return False
    if not os.path.isfile(obj_path):
        print(f"  OBJ not found: {obj_path}")
        return False

    print(f"  Importing OBJ: {obj_path}")
    bpy.ops.import_scene.obj(filepath=obj_path, axis_forward="-Z", axis_up="Y")
    return True


def import_stl(stl_path):
    """Fallback: import an STL file. Returns True on success."""
    if bpy is None:
        return False
    if not os.path.isfile(stl_path):
        print(f"  STL not found: {stl_path}")
        return False

    print(f"  Importing STL fallback: {stl_path}")
    bpy.ops.import_mesh.stl(filepath=l_path)
    return True


def assign_materials(config=None):
    """Assign materials to imported objects based on OBJ group name conventions."""
    if bpy is None:
        return

    materials = create_all_materials()

    for obj in bpy.context.scene.objects:
        if obj.type != "MESH":
            continue

        label = obj.name.lower()
        mat_name = "Solid_Generic"

        for key, mapped_name in OBJ_GROUP_MATERIAL_MAP.items():
            if f"_{key}" in label:
                mat_name = mapped_name
                break

        if config and "obj_group_materials" in config:
            for key, mapped_name in config["obj_group_materials"].items():
                if f"_{key}" in label:
                    mat_name = mapped_name
                    break

        if mat_name in materials:
            if obj.data.materials:
                obj.data.materials[0] = materials[mat_name]
            else:
                obj.data.materials.append(materials[mat_name])


def add_lighting(config=None):
    """Add sun lamp and fill light to the scene."""
    if bpy is None:
        return

    sun_cfg = (config or {}).get("lighting", {}).get("sun", {})
    fill_cfg = (config or {}).get("lighting", {}).get("fill", {})

    sun_data = bpy.data.lights.new(name="Sun_Light", type="SUN")
    sun_data.energy = sun_cfg.get("energy", 3.0)
    color = sun_cfg.get("color", [1.0, 0.95, 0.85])
    sun_data.color = color
    sun_angle = sun_cfg.get("angle_deg", 45)
    sun_object = bpy.data.objects.new("Sun_Light", sun_data)
    bpy.context.collection.objects.link(sun_object)
    rot = sun_cfg.get("rotation_euler", [0.785, 0.0, 0.524])
    sun_object.rotation_euler = rot
    print(f"  Added sun light (energy={sun_data.energy})")

    fill_data = bpy.data.lights.new(name="Fill_Light", type="AREA")
    fill_data.energy = fill_cfg.get("energy", 1.0)
    fill_data.size = fill_cfg.get("size", 5.0)
    fill_data.color = fill_cfg.get("color", [0.85, 0.90, 1.0])
    fill_object = bpy.data.objects.new("Fill_Light", fill_data)
    bpy.context.collection.objects.link(fill_object)
    loc = fill_cfg.get("location", [2.0, -5.0, 12.0])
    fill_object.location = loc
    fill_object.rotation_euler = fill_cfg.get("rotation_euler", [0.785, 0.0, 0.0])
    print(f"  Added fill light (energy={fill_data.energy})")


def add_camera(config=None):
    """Add a camera targeted at the building center."""
    if bpy is None:
        return

    cam_cfg = (config or {}).get("camera", {})
    lens = cam_cfg.get("lens_mm", 50)

    cam_data = bpy.data.cameras.new(name="Tubehouse_Camera")
    cam_data.lens = lens
    cam_data.type = cam_cfg.get("type", "PERSP")

    cam_object = bpy.data.objects.new("Tubehouse_Camera", cam_data)
    bpy.context.collection.objects.link(cam_object)

    loc = cam_cfg.get("location", [8.0, -8.0, 14.0])
    cam_object.location = Vector(loc) if Vector else loc

    all_x = []
    all_y = []
    all_z = []
    for obj in bpy.context.scene.objects:
        if obj.type == "MESH":
            for corner in obj.bound_box:
                all_x.append(corner[0] + obj.location.x)
                all_y.append(corner[1] + obj.location.y)
                all_z.append(corner[2] + obj.location.z)

    if all_x:
        center = Vector(
            ((min(all_x) + max(all_x)) / 2,
             (min(all_y) + max(all_y)) / 2,
             (min(all_z) + max(all_z)) / 2)
        ) if Vector else (
            (min(all_x) + max(all_x)) / 2,
            (min(all_y) + max(all_y)) / 2,
            (min(all_z) + max(all_z)) / 2,
        )
    else:
        center = Vector((2.0, 12.5, 8.0)) if Vector else (2.0, 12.5, 8.0)

    direction = Vector(loc) - center if Vector else None
    if direction and Vector:
        rot_quat = direction.normalized().to_track_quat("-Z", "Y")
        cam_object.rotation_euler = rot_quat.to_euler()
    else:
        cam_object.rotation_euler = (1.1, 0.0, 0.785)

    bpy.context.scene.camera = cam_object
    print(f"  Added camera (lens={lens}mm")


def save_scene(output_path):
    """Save the current Blender scene to a .blend file."""
    if bpy is None:
        print("  ERROR: bpy not available, cannot save.")
        return False

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=output_path)
    print(f"  Saved scene: {output_path}")
    return True


def main():
    """Entry point: load OBJ, assign materials, add lights/camera, save."""
    print(f"\n{'=' * 60}")
    print("setup_blender_scene: assembling Blender scene")
    print(f"{'=' * 60}")

    config = load_config()

    if bpy is None:
        print("ERROR: This script must be run inside Blender.")
        print("  Usage: blender --background --python src/setup_blender_scene.py")
        return False

    print("  Clearing default scene...")
    clear_scene()

    obj_path = os.environ.get("TUBEHOUSE_OBJ", OBJ_COMBINED)
    stl_path = os.environ.get("TUBEHOUSE_STL", STL_FALLBACK)

    if os.path.isfile(obj_path):
        if not import_obj(obj_path):
            print("  OBJ import failed, trying STL fallback...")
            if os.path.isfile(stl_path):
                import_stl(stl_path)
            else:
                print("  No importable geometry found. Exiting.")
                return False
    elif os.path.isfile(stl_path):
        print("  OBJ not found, falling back to STL...")
        import_stl(stl_path)
    else:
        print(f"  No geometry found at {obj_path} or {stl_path}")
        print("  Run the FreeCAD generator first: ./run.sh")
        return False

    print("  Assigning materials...")
    assign_materials(config)

    print("  Adding lighting...")
    add_lighting(config)

    print("  Adding camera...")
    add_camera(config)

    blend_path = os.environ.get(
        "TUBEHOUSE_BLEND",
        os.path.join(OUT_DIR, "tubehouse_scene.blend"),
    )
    success = save_scene(blend_path)

    if not success:
        return False

    print(f"\n  Scene ready: {blend_path}")
    print("  Next steps:")
    print("    blender --background tubehouse_scene.blend --python src/render_blender.py")
    return True


if __name__ == "__main__":
    main()