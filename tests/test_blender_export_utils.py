import unittest
import os
import tempfile
import math

from src.blender_export_utils import (
    obj_group_name,
    obj_path_for_floor,
    obj_path_for_combined,
    write_mtl,
    MATERIAL_PALETTE,
    _compute_face_normals,
    _is_3d_solid,
)


class ObjGroupNameTest(unittest.TestCase):
    def test_wall_group(self):
        self.assertEqual(obj_group_name(0, "WALLS"), "F0_wall")

    def test_room_group(self):
        self.assertEqual(obj_group_name(1, "ROOMS"), "F1_room")

    def test_stair_group(self):
        self.assertEqual(obj_group_name(2, "STAIRS"), "F2_stair")

    def test_symbol_group(self):
        self.assertEqual(obj_group_name(3, "SYMBOLS"), "F3_symbol")

    def test_solid_group(self):
        self.assertEqual(obj_group_name(4, "3D_MODEL"), "F4_solid")

    def test_unknown_key_falls_back_to_lower(self):
        self.assertEqual(obj_group_name(0, "CUSTOM"), "F0_custom")


class ObjPathTest(unittest.TestCase):
    def test_floor_path(self):
        path = obj_path_for_floor("/tmp/out/obj", 0)
        self.assertTrue(path.replace("\\", "/").endswith("/tmp/out/obj/floorplan_F0.obj"))

    def test_floor_path_higher_level(self):
        path = obj_path_for_floor("/tmp/out/obj", 3)
        self.assertTrue(path.replace("\\", "/").endswith("/tmp/out/obj/floorplan_F3.obj"))

    def test_combined_path(self):
        path = obj_path_for_combined("/tmp/out/obj")
        self.assertTrue(path.replace("\\", "/").endswith("/tmp/out/obj/tubehouse_full_3d.obj"))


class WriteMtlTest(unittest.TestCase):
    def test_writes_mtl_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            mtl_path = os.path.join(tmpdir, "test.mtl")
            result = write_mtl(mtl_path)
            self.assertEqual(result, mtl_path)
            self.assertTrue(os.path.isfile(mtl_path))

            with open(mtl_path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("newmtl Concrete_Wall", content)
            self.assertIn("newmtl Room_Fill", content)
            self.assertIn("newmtl Stair_Concrete", content)
            self.assertIn("newmtl Floor_Slab", content)

    def test_custom_palette(self):
        custom = {"wall": {"Kd": (1.0, 0.0, 0.0), "name": "Red_Wall"}}
        with tempfile.TemporaryDirectory() as tmpdir:
            mtl_path = os.path.join(tmpdir, "custom.mtl")
            write_mtl(mtl_path, palette=custom)
            with open(mtl_path, encoding="utf-8") as fh:
                content = fh.read()
            self.assertIn("newmtl Red_Wall", content)
            self.assertIn("Kd 1.0000 0.0000 0.0000", content)


class MaterialPaletteTest(unittest.TestCase):
    def test_all_expected_keys_present(self):
        for key in ("wall", "room", "stair", "symbol", "solid", "slab"):
            self.assertIn(key, MATERIAL_PALETTE)
            self.assertIn("name", MATERIAL_PALETTE[key])
            self.assertIn("Kd", MATERIAL_PALETTE[key])
            self.assertEqual(len(MATERIAL_PALETTE[key]["Kd"]), 3)

    def test_kd_values_in_range(self):
        for key, mat in MATERIAL_PALETTE.items():
            for val in mat["Kd"]:
                self.assertGreaterEqual(val, 0.0)
                self.assertLessEqual(val, 1.0)


class ComputeFaceNormalsTest(unittest.TestCase):
    def test_unit_length_normals(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        faces = [(0, 1, 2)]
        normals = _compute_face_normals(verts, faces)
        self.assertEqual(len(normals), 1)
        nx, ny, nz = normals[0]
        length = math.sqrt(nx * nx + ny * ny + nz * nz)
        self.assertAlmostEqual(length, 1.0, places=6)

    def test_upward_normal_for_z_up_triangle(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0)]
        faces = [(0, 1, 2)]
        normals = _compute_face_normals(verts, faces)
        nx, ny, nz = normals[0]
        self.assertGreater(nz, 0.0)

    def test_degenerate_triangle_gives_fallback(self):
        verts = [(0, 0, 0), (0, 0, 0), (0, 0, 0)]
        faces = [(0, 1, 2)]
        normals = _compute_face_normals(verts, faces)
        self.assertEqual(len(normals), 1)
        self.assertAlmostEqual(normals[0][2], 1.0, places=6)

    def test_multiple_faces(self):
        verts = [(0, 0, 0), (1, 0, 0), (0, 1, 0), (1, 1, 0)]
        faces = [(0, 1, 2), (1, 3, 2)]
        normals = _compute_face_normals(verts, faces)
        self.assertEqual(len(normals), 2)

    def test_cube_normals_different_directions(self):
        verts = [
            (0, 0, 0), (1, 0, 0), (1, 1, 0), (0, 1, 0),
            (0, 0, 1), (1, 0, 1), (1, 1, 1), (0, 1, 1),
        ]
        faces = [
            (0, 1, 2), (0, 2, 3),
            (4, 6, 5), (4, 7, 6),
            (0, 4, 5), (0, 5, 1),
            (2, 6, 7), (2, 7, 3),
            (0, 3, 7), (0, 7, 4),
            (1, 5, 6), (1, 6, 2),
        ]
        normals = _compute_face_normals(verts, faces)
        self.assertEqual(len(normals), 12)
        for nx, ny, nz in normals:
            length = math.sqrt(nx * nx + ny * ny + nz * nz)
            self.assertAlmostEqual(length, 1.0, places=6)


class Is3dSolidTest(unittest.TestCase):
    def test_none_shape(self):
        class FakeObj:
            pass
        obj = FakeObj()
        self.assertFalse(_is_3d_solid(obj))

    def test_no_shape_attr(self):
        class FakeObj:
            pass
        obj = FakeObj()
        self.assertFalse(_is_3d_solid(obj))

    def test_shape_with_solids(self):
        class FakeShape:
            Solids = [True]
            Volume = 100
        class FakeObj:
            Shape = FakeShape()
        self.assertTrue(_is_3d_solid(FakeObj()))

    def test_shape_with_positive_volume(self):
        class FakeShape:
            Solids = []
            Volume = 50
        class FakeObj:
            Shape = FakeShape()
        self.assertTrue(_is_3d_solid(FakeObj()))

    def test_shape_empty(self):
        class FakeShape:
            Solids = []
            Volume = 0
        class FakeObj:
            Shape = FakeShape()
        self.assertFalse(_is_3d_solid(FakeObj()))


if __name__ == "__main__":
    unittest.main()