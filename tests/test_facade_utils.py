import unittest

from src.facade_utils import floor_elevation_bands, front_facade_features


class FacadeUtilsTest(unittest.TestCase):
    def test_floor_elevation_bands_use_cumulative_floor_heights(self):
        floors = [
            {"level": 0, "name": "Ground Floor", "floor_to_ceiling_mm": 3500},
            {"level": 1, "name": "First Floor", "floor_to_ceiling_mm": 3500},
            {"level": 2, "name": "Second Floor", "floor_to_ceiling_mm": 3200},
        ]

        self.assertEqual(
            floor_elevation_bands(floors),
            [
                {
                    "level": 0,
                    "name": "Ground Floor",
                    "base_z_mm": 0,
                    "top_z_mm": 3500,
                    "height_mm": 3500,
                },
                {
                    "level": 1,
                    "name": "First Floor",
                    "base_z_mm": 3500,
                    "top_z_mm": 7000,
                    "height_mm": 3500,
                },
                {
                    "level": 2,
                    "name": "Second Floor",
                    "base_z_mm": 7000,
                    "top_z_mm": 10200,
                    "height_mm": 3200,
                },
            ],
        )

    def test_front_facade_features_detect_balcony_and_front_windows_only(self):
        floor = {
            "level": 1,
            "name": "First Floor",
            "floor_to_ceiling_mm": 3500,
            "zones": [
                {"id": "balcony", "y_start": 0, "y_end": 2000},
                {"id": "living", "y_start": 2000, "y_end": 7000},
            ],
            "elements": [
                {
                    "type": "window",
                    "id": "front_left",
                    "x": 600,
                    "y": 0,
                    "width_mm": 800,
                },
                {
                    "type": "window",
                    "id": "internal",
                    "x": 300,
                    "y": 2000,
                    "width_mm": 900,
                },
            ],
            "doors": [
                {
                    "type": "sliding",
                    "id": "balcony_door",
                    "x": 700,
                    "y": 2000,
                    "width_mm": 2000,
                },
            ],
        }

        self.assertEqual(
            front_facade_features(floor),
            {
                "level": 1,
                "name": "First Floor",
                "height_mm": 3500,
                "has_front_balcony": True,
                "openings": [
                    {
                        "id": "front_left",
                        "kind": "window",
                        "x": 600,
                        "width_mm": 800,
                        "sill_mm": 900,
                        "height_mm": 1800,
                    }
                ],
            },
        )

    def test_front_facade_features_promote_wide_front_window_to_glazing(self):
        floor = {
            "level": 4,
            "name": "Rooftop",
            "floor_to_ceiling_mm": 3200,
            "zones": [],
            "elements": [
                {
                    "type": "window",
                    "id": "sky_lounge_front_glazing",
                    "x": 400,
                    "y": 0,
                    "width_mm": 3200,
                    "note": "Full-height glazing: front facade of sky lounge",
                }
            ],
            "doors": [],
        }

        self.assertEqual(
            front_facade_features(floor),
            {
                "level": 4,
                "name": "Rooftop",
                "height_mm": 3200,
                "has_front_balcony": False,
                "openings": [
                    {
                        "id": "sky_lounge_front_glazing",
                        "kind": "glazing",
                        "x": 400,
                        "width_mm": 3200,
                        "sill_mm": 200,
                        "height_mm": 2600,
                    }
                ],
            },
        )

    def test_front_facade_features_include_ground_floor_garage_opening(self):
        floor = {
            "level": 0,
            "name": "Ground Floor",
            "floor_to_ceiling_mm": 3500,
            "zones": [],
            "elements": [],
            "doors": [
                {
                    "type": "garage_opening",
                    "id": "garage_door",
                    "x": 600,
                    "y": 0,
                    "width_mm": 2800,
                }
            ],
        }

        self.assertEqual(
            front_facade_features(floor),
            {
                "level": 0,
                "name": "Ground Floor",
                "height_mm": 3500,
                "has_front_balcony": False,
                "openings": [
                    {
                        "id": "garage_door",
                        "kind": "garage_opening",
                        "x": 600,
                        "width_mm": 2800,
                        "sill_mm": 0,
                        "height_mm": 2800,
                    }
                ],
            },
        )


if __name__ == "__main__":
    unittest.main()
