import unittest

from src.floorplan_utils import cumulative_floor_offsets, total_building_height_mm


class FloorplanUtilsTest(unittest.TestCase):
    def test_cumulative_offsets_use_actual_floor_heights(self):
        floors = [
            {"level": 0, "floor_to_ceiling_mm": 3500},
            {"level": 1, "floor_to_ceiling_mm": 3500},
            {"level": 2, "floor_to_ceiling_mm": 3500},
            {"level": 3, "floor_to_ceiling_mm": 3200},
            {"level": 4, "floor_to_ceiling_mm": 3200},
        ]

        self.assertEqual(
            cumulative_floor_offsets(floors),
            {0: 0, 1: 3500, 2: 7000, 3: 10500, 4: 13700},
        )

    def test_total_height_uses_actual_floor_heights(self):
        floors = [
            {"level": 0, "floor_to_ceiling_mm": 3500},
            {"level": 1, "floor_to_ceiling_mm": 3200},
            {"level": 2},
        ]

        self.assertEqual(total_building_height_mm(floors), 9900)


if __name__ == "__main__":
    unittest.main()
