"""Pure-Python tests for IFC export (no FreeCAD/Blender needed)."""

import json
import os
import sys
import tempfile
import unittest

SCRIPT_DIR = os.path.join(os.path.dirname(__file__), os.pardir, "src")
SCRIPT_DIR = os.path.normpath(SCRIPT_DIR)
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

import ifcopenshell

from floorplan_utils import cumulative_floor_offsets
from ifc_export_utils import (
    create_ifc_doors,
    create_ifc_project,
    create_ifc_spaces,
    create_ifc_storeys,
    create_ifc_walls,
    export_ifc,
    export_ifc_from_spec_file,
    _wall_thickness_mm,
)

SPEC_PATH = os.path.join(
    os.path.dirname(__file__), os.pardir, "spec", "floorplan-spec.json"
)
SPEC_PATH = os.path.normpath(SPEC_PATH)

with open(SPEC_PATH, encoding="utf-8") as f:
    SPEC = json.load(f)


class IfcProjectTest(unittest.TestCase):
    def test_creates_project_and_site(self):
        model, project, site, building, body = create_ifc_project(SPEC)
        self.assertEqual(project.is_a(), "IfcProject")
        self.assertEqual(project.Name, SPEC["project"]["name"])
        self.assertEqual(site.is_a(), "IfcSite")

    def test_creates_building(self):
        _, _, _, building, _ = create_ifc_project(SPEC)
        self.assertEqual(building.is_a(), "IfcBuilding")

    def test_has_body_context(self):
        _, _, _, _, body = create_ifc_project(SPEC)
        self.assertEqual(body.ContextType, "Model")
        self.assertEqual(body.ContextIdentifier, "Body")


class IfcStoreysTest(unittest.TestCase):
    def test_five_storeys_created(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        self.assertEqual(len(storeys), 5)

    def test_storey_elevations_match_offsets(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        z_offsets = cumulative_floor_offsets(SPEC["floors"])
        for floor, storey in zip(SPEC["floors"], storeys):
            expected_m = z_offsets[floor["level"]] / 1000.0
            self.assertAlmostEqual(storey.Elevation, expected_m, places=3)

    def test_storey_names(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        names = [s.Name for s in storeys]
        self.assertIn("Ground Floor", names)
        self.assertIn("Rooftop", names)


class IfcWallsTest(unittest.TestCase):
    def test_walls_created_per_floor(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        walls = create_ifc_walls(model, SPEC, storeys, body)
        expected = sum(len(f.get("walls", [])) for f in SPEC["floors"])
        self.assertEqual(len(walls), expected)

    def test_wall_thickness_exterior(self):
        wall = {"type": "exterior", "w": 200, "h": 25000}
        self.assertEqual(_wall_thickness_mm(SPEC, wall), 200)

    def test_wall_thickness_interior_horizontal(self):
        wall = {"type": "partition", "w": 2000, "h": 100}
        self.assertEqual(_wall_thickness_mm(SPEC, wall), 100)

    def test_wall_thickness_interior_vertical(self):
        wall = {"type": "partition", "w": 100, "h": 3900}
        self.assertEqual(_wall_thickness_mm(SPEC, wall), 100)

    def test_all_walls_are_ifcwall(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        walls = create_ifc_walls(model, SPEC, storeys, body)
        for w in walls:
            self.assertEqual(w.is_a(), "IfcWall")


class IfcSpacesTest(unittest.TestCase):
    def test_spaces_created_per_floor(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        spaces = create_ifc_spaces(model, SPEC, storeys, body)
        expected = sum(len(f.get("rooms", [])) for f in SPEC["floors"])
        self.assertEqual(len(spaces), expected)

    def test_all_spaces_are_ifcspace(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        spaces = create_ifc_spaces(model, SPEC, storeys, body)
        for s in spaces:
            self.assertEqual(s.is_a(), "IfcSpace")


class IfcDoorsTest(unittest.TestCase):
    def test_doors_created_per_floor(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        doors = create_ifc_doors(model, SPEC, storeys, body)
        expected = sum(len(f.get("doors", [])) for f in SPEC["floors"])
        self.assertEqual(len(doors), expected)

    def test_all_doors_are_ifcdoor(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        doors = create_ifc_doors(model, SPEC, storeys, body)
        for d in doors:
            self.assertEqual(d.is_a(), "IfcDoor")

    def test_door_has_overall_width(self):
        model, _, _, building, body = create_ifc_project(SPEC)
        storeys = create_ifc_storeys(model, SPEC, building, body)
        doors = create_ifc_doors(model, SPEC, storeys, body)
        for d in doors:
            self.assertGreater(d.OverallWidth, 0)


class ExportIfcIntegrationTest(unittest.TestCase):
    def test_writes_valid_ifc_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "test.ifc")
            result = export_ifc(SPEC, out_path)
            self.assertTrue(os.path.isfile(out_path))
            self.assertGreater(os.path.getsize(out_path), 0)

            model = ifcopenshell.open(out_path)
            self.assertEqual(len(model.by_type("IfcProject")), 1)
            self.assertEqual(len(model.by_type("IfcSite")), 1)
            self.assertEqual(len(model.by_type("IfcBuilding")), 1)

    def test_export_counts_match_spec(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "test.ifc")
            result = export_ifc(SPEC, out_path)
            self.assertEqual(result["storeys"], 5)

            expected_walls = sum(len(f.get("walls", [])) for f in SPEC["floors"])
            self.assertEqual(result["walls"], expected_walls)

            expected_spaces = sum(len(f.get("rooms", [])) for f in SPEC["floors"])
            self.assertEqual(result["spaces"], expected_spaces)

            expected_doors = sum(len(f.get("doors", [])) for f in SPEC["floors"])
            self.assertEqual(result["doors"], expected_doors)

    def test_from_spec_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "from_spec.ifc")
            result = export_ifc_from_spec_file(SPEC_PATH, out_path)
            self.assertTrue(os.path.isfile(out_path))
            self.assertEqual(result["storeys"], 5)

    def test_read_back_storey_elevations(self):
        with tempfile.TemporaryDirectory() as tmp:
            out_path = os.path.join(tmp, "elev.ifc")
            export_ifc(SPEC, out_path)
            model = ifcopenshell.open(out_path)
            storeys = model.by_type("IfcBuildingStorey")
            z_offsets = cumulative_floor_offsets(SPEC["floors"])
            for floor, storey in zip(SPEC["floors"], sorted(storeys, key=lambda s: s.Elevation)):
                expected_m = z_offsets[floor["level"]] / 1000.0
                self.assertAlmostEqual(storey.Elevation, expected_m, places=2)


if __name__ == "__main__":
    unittest.main()
