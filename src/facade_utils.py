"""Pure helpers for deriving front facade data from the floorplan spec."""

try:
    from .floorplan_utils import cumulative_floor_offsets, floor_height_mm
except ImportError:  # pragma: no cover - script-style import inside FreeCAD
    from floorplan_utils import cumulative_floor_offsets, floor_height_mm


def floor_elevation_bands(floor_specs, default_floor_height_m=3.2):
    """Return front elevation vertical bands for each floor."""
    offsets = cumulative_floor_offsets(floor_specs, default_floor_height_m)
    bands = []

    for floor in sorted(floor_specs, key=lambda item: item["level"]):
        height_mm = floor_height_mm(floor, default_floor_height_m)
        base_z_mm = offsets[floor["level"]]
        bands.append(
            {
                "level": floor["level"],
                "name": floor["name"],
                "base_z_mm": base_z_mm,
                "top_z_mm": base_z_mm + height_mm,
                "height_mm": height_mm,
            }
        )

    return bands


def _has_front_balcony(floor):
    return any(
        zone.get("id") == "balcony" and zone.get("y_start", 1) == 0
        for zone in floor.get("zones", [])
    )


def _opening_height_for_window(window):
    note = (window.get("note") or "").lower()
    if "full-height glazing" in note or window.get("width_mm", 0) >= 3000:
        return "glazing", 200, 2600
    return "window", 900, 1800


def front_facade_features(floor, default_floor_height_m=3.2):
    """Return a simplified facade description for one floor."""
    openings = []

    for element in floor.get("elements", []):
        if element.get("type") != "window" or element.get("y") != 0:
            continue
        kind, sill_mm, height_mm = _opening_height_for_window(element)
        openings.append(
            {
                "id": element["id"],
                "kind": kind,
                "x": element["x"],
                "width_mm": element["width_mm"],
                "sill_mm": sill_mm,
                "height_mm": height_mm,
            }
        )

    for door in floor.get("doors", []):
        if door.get("type") == "garage_opening":
            openings.append(
                {
                    "id": door["id"],
                    "kind": "garage_opening",
                    "x": door["x"],
                    "width_mm": door["width_mm"],
                    "sill_mm": 0,
                    "height_mm": 2800,
                }
            )

    openings.sort(key=lambda item: (item["x"], item["id"]))

    return {
        "level": floor["level"],
        "name": floor["name"],
        "height_mm": floor_height_mm(floor, default_floor_height_m),
        "has_front_balcony": _has_front_balcony(floor),
        "openings": openings,
    }
