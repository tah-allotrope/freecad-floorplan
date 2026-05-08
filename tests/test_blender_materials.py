import unittest
import os
import json

from src.blender_materials import (
    MATERIAL_DEFINITIONS,
    ROOM_MATERIAL_MAP,
    ZONE_MATERIAL_MAP,
    OBJ_GROUP_MATERIAL_MAP,
    material_name_for_room,
    material_name_for_zone,
    material_name_for_obj_group,
    get_material_definition,
)


class MaterialDefinitionsTest(unittest.TestCase):
    def test_all_definitions_have_required_keys(self):
        for name, defn in MATERIAL_DEFINITIONS.items():
            self.assertIn("base_color", defn, f"{name} missing base_color")
            self.assertIn("roughness", defn, f"{name} missing roughness")
            self.assertIn("metallic", defn, f"{name} missing metallic")
            self.assertEqual(len(defn["base_color"]), 4, f"{name} base_color must be RGBA")

    def test_base_color_values_in_range(self):
        for name, defn in MATERIAL_DEFINITIONS.items():
            for val in defn["base_color"]:
                self.assertGreaterEqual(val, 0.0, f"{name} base_color out of range")
                self.assertLessEqual(val, 1.0, f"{name} base_color out of range")

    def test_roughness_and_metallic_in_range(self):
        for name, defn in MATERIAL_DEFINITIONS.items():
            self.assertGreaterEqual(defn["roughness"], 0.0)
            self.assertLessEqual(defn["roughness"], 1.0)
            self.assertGreaterEqual(defn["metallic"], 0.0)
            self.assertLessEqual(defn["metallic"], 1.0)

    def test_glass_material_has_transmission(self):
        glass = MATERIAL_DEFINITIONS["Glass_Glazing"]
        self.assertGreater(glass.get("transmission", 0), 0)
        self.assertGreater(glass.get("ior", 0), 1.0)

    def test_steel_material_is_metallic(self):
        steel = MATERIAL_DEFINITIONS["Steel_Railing"]
        self.assertGreater(steel["metallic"], 0.5)


class MaterialNameLookupsTest(unittest.TestCase):
    def test_room_lookup_known(self):
        self.assertEqual(material_name_for_room("bathroom"), "Tile_Bathroom")
        self.assertEqual(material_name_for_room("kitchen"), "Tile_Bathroom")
        self.assertEqual(material_name_for_room("bedroom"), "Wood_Flooring")
        self.assertEqual(material_name_for_room("parking"), "Concrete_Wall")

    def test_room_lookup_unknown_falls_back(self):
        self.assertEqual(material_name_for_room("unknown_room"), "Room_Fill")

    def test_zone_lookup_known(self):
        self.assertEqual(material_name_for_zone("core"), "Steel_Railing")
        self.assertEqual(material_name_for_zone("balcony"), "Concrete_Wall")
        self.assertEqual(material_name_for_zone("rear_void"), "Glass_Glazing")

    def test_zone_lookup_unknown_falls_back(self):
        self.assertEqual(material_name_for_zone("nonexistent"), "Room_Fill")

    def test_obj_group_lookup_known(self):
        self.assertEqual(material_name_for_obj_group("wall"), "Concrete_Wall")
        self.assertEqual(material_name_for_obj_group("room"), "Room_Fill")
        self.assertEqual(material_name_for_obj_group("stair"), "Stair_Concrete")
        self.assertEqual(material_name_for_obj_group("slab"), "Floor_Slab")

    def test_obj_group_lookup_unknown_falls_back(self):
        self.assertEqual(material_name_for_obj_group("custom_tag"), "Solid_Generic")


class GetMaterialDefinitionTest(unittest.TestCase):
    def test_known_definition(self):
        defn = get_material_definition("Concrete_Wall")
        self.assertEqual(defn["roughness"], 0.75)
        self.assertEqual(defn["metallic"], 0.0)

    def test_unknown_returns_solid_generic(self):
        defn = get_material_definition("nonexistent_material")
        self.assertEqual(defn, MATERIAL_DEFINITIONS["Solid_Generic"])


class BlenderMaterialsJsonTest(unittest.TestCase):
    def test_json_file_exists_and_is_valid(self):
        spec_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "spec",
            "blender_materials.json",
        )
        self.assertTrue(os.path.isfile(spec_path), f"Missing: {spec_path}")
        with open(spec_path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertIn("room_materials", data)
        self.assertIn("zone_materials", data)
        self.assertIn("obj_group_materials", data)
        self.assertIn("lighting", data)
        self.assertIn("camera", data)
        self.assertIn("render", data)

    def test_json_materials_match_python_definitions(self):
        spec_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "spec",
            "blender_materials.json",
        )
        with open(spec_path, encoding="utf-8") as fh:
            data = json.load(fh)

        for room_id, mat_name in data["room_materials"].items():
            self.assertIn(mat_name, MATERIAL_DEFINITIONS,
                          f"JSON room_materials.{room_id} references unknown material: {mat_name}")

        for zone_id, mat_name in data["zone_materials"].items():
            self.assertIn(mat_name, MATERIAL_DEFINITIONS,
                          f"JSON zone_materials.{zone_id} references unknown material: {mat_name}")

        for group_key, mat_name in data["obj_group_materials"].items():
            self.assertIn(mat_name, MATERIAL_DEFINITIONS,
                          f"JSON obj_group_materials.{group_key} references unknown material: {mat_name}")

    def test_json_room_materials_match_python(self):
        for key, value in ROOM_MATERIAL_MAP.items():
            self.assertIn(value, MATERIAL_DEFINITIONS, f"Python ROOM_MATERIAL_MAP.{key} references unknown material: {value}")
        spec_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "spec",
            "blender_materials.json",
        )
        with open(spec_path, encoding="utf-8") as fh:
            data = json.load(fh)
        for key, value in data["room_materials"].items():
            self.assertEqual(value, ROOM_MATERIAL_MAP.get(key), f"JSON/Python mismatch for room: {key}")


if __name__ == "__main__":
    unittest.main()