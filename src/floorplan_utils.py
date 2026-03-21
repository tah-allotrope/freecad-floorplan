"""Pure helpers for floorplan generation logic."""


def floor_height_mm(floor, default_floor_height_m=3.2):
    """Return a floor's height in millimetres."""
    return int(floor.get("floor_to_ceiling_mm", default_floor_height_m * 1000))


def cumulative_floor_offsets(floor_specs, default_floor_height_m=3.2):
    """Return a mapping of floor level to cumulative Z offset in millimetres."""
    offsets = {}
    current_offset = 0

    for floor in sorted(floor_specs, key=lambda item: item["level"]):
        offsets[floor["level"]] = current_offset
        current_offset += floor_height_mm(floor, default_floor_height_m)

    return offsets


def total_building_height_mm(floor_specs, default_floor_height_m=3.2):
    """Return the total building height in millimetres."""
    return sum(floor_height_mm(floor, default_floor_height_m) for floor in floor_specs)
