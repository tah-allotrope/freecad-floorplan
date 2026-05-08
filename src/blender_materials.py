"""Blender material palette for the tubehouse visualization.

Provides pure-Python material definitions (usable in tests) and
Blender-side material creation via Principled BSDF nodes.

Each material is defined as a dict with RGBA base color and PBR
parameters.  The JSON sidecar (spec/blender_materials.json) maps
room IDs and zone IDs to material names.
"""

MATERIAL_DEFINITIONS = {
    "Concrete_Wall": {
        "base_color": (0.78, 0.76, 0.72, 1.0),
        "roughness": 0.75,
        "metallic": 0.0,
        "description": "Exposed concrete for structural walls",
    },
    "Room_Fill": {
        "base_color": (0.95, 0.95, 0.93, 1.0),
        "roughness": 0.60,
        "metallic": 0.0,
        "description": "Generic interior room fill",
    },
    "Stair_Concrete": {
        "base_color": (0.60, 0.58, 0.55, 1.0),
        "roughness": 0.80,
        "metallic": 0.0,
        "description": "Concrete for stair treads and landings",
    },
    "Floor_Slab": {
        "base_color": (0.70, 0.68, 0.65, 1.0),
        "roughness": 0.70,
        "metallic": 0.0,
        "description": "Floor slab concrete",
    },
    "Solid_Generic": {
        "base_color": (0.85, 0.83, 0.80, 1.0),
        "roughness": 0.65,
        "metallic": 0.0,
        "description": "Default 3D solid material",
    },
    "Symbol_Line": {
        "base_color": (0.90, 0.90, 0.90, 1.0),
        "roughness": 0.50,
        "metallic": 0.0,
        "description": "2D symbol overlays",
    },
    "Glass_Glazing": {
        "base_color": (0.70, 0.85, 0.95, 0.30),
        "roughness": 0.05,
        "metallic": 0.0,
        "transmission": 0.90,
        "ior": 1.52,
        "description": "Window glazing with high transmission",
    },
    "Steel_Railing": {
        "base_color": (0.45, 0.47, 0.50, 1.0),
        "roughness": 0.30,
        "metallic": 0.85,
        "description": "Balcony and stair railing steel",
    },
    "Wood_Flooring": {
        "base_color": (0.62, 0.44, 0.28, 1.0),
        "roughness": 0.55,
        "metallic": 0.0,
        "description": "Interior wood flooring",
    },
    "Tile_Bathroom": {
        "base_color": (0.80, 0.86, 0.90, 1.0),
        "roughness": 0.20,
        "metallic": 0.0,
        "description": "Bathroom tile finish",
    },
}

ROOM_MATERIAL_MAP = {
    "parking": "Concrete_Wall",
    "commercial": "Room_Fill",
    "lift_shaft": "Steel_Railing",
    "staircase": "Stair_Concrete",
    "core_void": "Glass_Glazing",
    "utility": "Concrete_Wall",
    "bathroom": "Tile_Bathroom",
    "ensuite": "Tile_Bathroom",
    "rear_void": "Glass_Glazing",
    "bedroom": "Wood_Flooring",
    "living": "Wood_Flooring",
    "kitchen": "Tile_Bathroom",
    "balcony": "Concrete_Wall",
    "terrace": "Concrete_Wall",
    "living_room": "Wood_Flooring",
    "working_room": "Wood_Flooring",
    "master_bedroom": "Wood_Flooring",
    "bedroom_2": "Wood_Flooring",
    "laundry": "Tile_Bathroom",
}

ZONE_MATERIAL_MAP = {
    "parking": "Concrete_Wall",
    "reception": "Room_Fill",
    "office": "Room_Fill",
    "storage": "Concrete_Wall",
    "core": "Steel_Railing",
    "staff": "Room_Fill",
    "balcony": "Concrete_Wall",
    "living": "Wood_Flooring",
    "dining": "Wood_Flooring",
    "library": "Wood_Flooring",
    "home_office": "Wood_Flooring",
    "bathroom": "Tile_Bathroom",
    "kitchen": "Tile_Bathroom",
    "rear_void": "Glass_Glazing",
}

OBJ_GROUP_MATERIAL_MAP = {
    "wall": "Concrete_Wall",
    "room": "Room_Fill",
    "stair": "Stair_Concrete",
    "symbol": "Symbol_Line",
    "solid": "Solid_Generic",
    "slab": "Floor_Slab",
}


def material_name_for_room(room_id):
    """Return the Blender material name for a room ID, or a fallback."""
    return ROOM_MATERIAL_MAP.get(room_id, "Room_Fill")


def material_name_for_zone(zone_id):
    """Return the Blender material name for a zone ID, or a fallback."""
    return ZONE_MATERIAL_MAP.get(zone_id, "Room_Fill")


def material_name_for_obj_group(group_key):
    """Return the Blender material name for an OBJ group convention key."""
    return OBJ_GROUP_MATERIAL_MAP.get(group_key, "Solid_Generic")


def get_material_definition(name):
    """Return the material definition dict for a named material."""
    return MATERIAL_DEFINITIONS.get(name, MATERIAL_DEFINITIONS["Solid_Generic"])


def create_blender_material(name, definition=None):
    """Create a Blender material with Principled BSDF from a definition.

    Must be called inside Blender (requires bpy).
    Returns the created material object.
    """
    import bpy

    if definition is None:
        definition = get_material_definition(name)

    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    mat.blend_method = "OPAQUE"

    if definition.get("transmission", 0) > 0:
        mat.blend_method = "ALPHA"

    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    bsdf = nodes.get("Principled BSDF")

    if bsdf is None:
        bsdf = nodes.new("ShaderNodeBsdfPrincipled")

    base_color = definition["base_color"]
    bsdf.inputs["Base Color"].default_value = base_color
    bsdf.inputs["Roughness"].default_value = definition.get("roughness", 0.65)
    bsdf.inputs["Metallic"].default_value = definition.get("metallic", 0.0)

    if definition.get("transmission", 0) > 0:
        bsdf.inputs["Alpha"].default_value = base_color[3]
        bsdf.inputs["Transmission"].default_value = definition["transmission"]
        bsdf.inputs["IOR"].default_value = definition.get("ior", 1.45)

    return mat


def create_all_materials():
    """Create all materials from MATERIAL_DEFINITIONS in the current Blender scene.

    Returns a dict mapping material name -> Blender material object.
    """
    materials = {}
    for name, definition in MATERIAL_DEFINITIONS.items():
        materials[name] = create_blender_material(name, definition)
    return materials