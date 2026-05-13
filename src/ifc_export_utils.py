"""IFC4 export from spec JSON via IfcOpenShell — no FreeCAD dependency."""

import json
import math
import os

import ifcopenshell
import ifcopenshell.api.aggregate
import ifcopenshell.api.context
import ifcopenshell.api.geometry
import ifcopenshell.api.project
import ifcopenshell.api.root
import ifcopenshell.api.spatial
import ifcopenshell.api.unit
from ifcopenshell.util.placement import a2p

from floorplan_utils import cumulative_floor_offsets


def _placement(x, y, z, angle_deg=0.0):
    cos_a = math.cos(math.radians(angle_deg))
    sin_a = math.sin(math.radians(angle_deg))
    return a2p((x, y, z), (0, 0, 1), (cos_a, sin_a, 0))


def create_ifc_project(spec):
    model = ifcopenshell.api.project.create_file()

    project = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcProject", name=spec["project"]["name"]
    )
    ifcopenshell.api.unit.assign_unit(model)

    ctx = ifcopenshell.api.context.add_context(model, context_type="Model")
    body = ifcopenshell.api.context.add_context(
        model,
        context_type="Model",
        context_identifier="Body",
        target_view="MODEL_VIEW",
        parent=ctx,
    )

    site = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcSite", name=spec["project"].get("location", "Site")
    )
    ifcopenshell.api.geometry.edit_object_placement(
        model, product=site, matrix=_placement(0, 0, 0)
    )

    building = ifcopenshell.api.root.create_entity(
        model, ifc_class="IfcBuilding", name=spec["project"]["name"]
    )

    ifcopenshell.api.aggregate.assign_object(model, relating_object=project, products=[site])
    ifcopenshell.api.aggregate.assign_object(model, relating_object=site, products=[building])

    return model, project, site, building, body


def create_ifc_storeys(model, spec, building, body):
    z_offsets = cumulative_floor_offsets(spec["floors"])
    storeys = []

    for floor in spec["floors"]:
        level = floor["level"]
        elevation_m = z_offsets[level] / 1000.0

        storey = ifcopenshell.api.root.create_entity(
            model,
            ifc_class="IfcBuildingStorey",
            name=floor["name"],
        )
        storey.Elevation = elevation_m

        ifcopenshell.api.aggregate.assign_object(
            model, relating_object=building, products=[storey]
        )
        ifcopenshell.api.geometry.edit_object_placement(
            model, product=storey, matrix=_placement(0, 0, elevation_m)
        )

        storeys.append(storey)

    return storeys


def _wall_thickness_mm(spec, wall):
    if wall["type"] == "exterior":
        return spec["wall_thickness"]["exterior_mm"]
    if wall["w"] > wall["h"]:
        return spec["wall_thickness"]["interior_horizontal_mm"]
    return spec["wall_thickness"]["interior_vertical_mm"]


def create_ifc_walls(model, spec, storeys, body):
    z_offsets = cumulative_floor_offsets(spec["floors"])
    all_walls = []

    for floor_idx, floor in enumerate(spec["floors"]):
        level = floor["level"]
        storey = storeys[floor_idx]
        z_offset_m = z_offsets[level] / 1000.0
        ceiling_h_m = floor.get("floor_to_ceiling_mm", 3500) / 1000.0

        for wall in floor.get("walls", []):
            x_m = wall["x"] / 1000.0
            y_m = wall["y"] / 1000.0
            w_m = wall["w"] / 1000.0
            h_m = wall["h"] / 1000.0
            thickness_m = _wall_thickness_mm(spec, wall) / 1000.0

            is_horizontal = w_m >= h_m
            length = w_m if is_horizontal else h_m

            ifc_wall = ifcopenshell.api.root.create_entity(
                model,
                ifc_class="IfcWall",
                name=wall.get("label", wall["id"]),
            )

            if is_horizontal:
                offset_x = x_m
                offset_y = y_m + h_m / 2.0 - thickness_m / 2.0
                angle = 0.0
            else:
                offset_x = x_m + w_m / 2.0 - thickness_m / 2.0
                offset_y = y_m
                angle = 90.0

            ifcopenshell.api.geometry.edit_object_placement(
                model, product=ifc_wall, matrix=_placement(offset_x, offset_y, z_offset_m, angle)
            )

            representation = ifcopenshell.api.geometry.add_wall_representation(
                model,
                context=body,
                length=length,
                height=ceiling_h_m,
                thickness=thickness_m,
            )
            ifcopenshell.api.geometry.assign_representation(
                model, product=ifc_wall, representation=representation
            )

            ifcopenshell.api.spatial.assign_container(
                model, relating_structure=storey, products=[ifc_wall]
            )

            all_walls.append(ifc_wall)

    return all_walls


def create_ifc_spaces(model, spec, storeys, body):
    z_offsets = cumulative_floor_offsets(spec["floors"])
    all_spaces = []

    for floor_idx, floor in enumerate(spec["floors"]):
        level = floor["level"]
        storey = storeys[floor_idx]
        z_offset_m = z_offsets[level] / 1000.0
        floor_h_m = floor.get("floor_to_ceiling_mm", 3500) / 1000.0

        for room in floor.get("rooms", []):
            x_m = room["x"] / 1000.0
            y_m = room["y"] / 1000.0
            w_m = room["w"] / 1000.0
            h_m = room["h"] / 1000.0

            space = ifcopenshell.api.root.create_entity(
                model,
                ifc_class="IfcSpace",
                name=room["name"],
            )

            ifcopenshell.api.geometry.edit_object_placement(
                model, product=space, matrix=_placement(x_m, y_m, z_offset_m)
            )

            representation = ifcopenshell.api.geometry.add_wall_representation(
                model,
                context=body,
                length=w_m,
                height=floor_h_m,
                thickness=h_m,
            )
            ifcopenshell.api.geometry.assign_representation(
                model, product=space, representation=representation
            )

            ifcopenshell.api.aggregate.assign_object(
                model, relating_object=storey, products=[space]
            )

            all_spaces.append(space)

    return all_spaces


def create_ifc_doors(model, spec, storeys, body):
    z_offsets = cumulative_floor_offsets(spec["floors"])
    all_doors = []

    for floor_idx, floor in enumerate(spec["floors"]):
        level = floor["level"]
        storey = storeys[floor_idx]
        z_offset_m = z_offsets[level] / 1000.0

        for door in floor.get("doors", []):
            width_m = door.get("width_mm", 800) / 1000.0

            if door["type"] == "swing":
                cx_m = door.get("arc_cx", door.get("leaf_x1", 0)) / 1000.0
                cy_m = door.get("arc_cy", door.get("leaf_y1", 0)) / 1000.0
            elif door["type"] == "sliding":
                cx_m = door.get("x", 0) / 1000.0
                cy_m = door.get("y", 0) / 1000.0
            elif door["type"] == "garage_opening":
                cx_m = (door.get("x", 0) + door.get("width_mm", 2000) / 2.0) / 1000.0
                cy_m = door.get("y", 0) / 1000.0
            else:
                cx_m = 0.0
                cy_m = 0.0

            ifc_door = ifcopenshell.api.root.create_entity(
                model,
                ifc_class="IfcDoor",
                name=door.get("id", "Door"),
            )
            ifc_door.OverallWidth = width_m
            ifc_door.OverallHeight = 2.1

            ifcopenshell.api.geometry.edit_object_placement(
                model, product=ifc_door, matrix=_placement(cx_m, cy_m, z_offset_m)
            )

            ifcopenshell.api.spatial.assign_container(
                model, relating_structure=storey, products=[ifc_door]
            )

            all_doors.append(ifc_door)

    return all_doors


def export_ifc(spec, output_path):
    model, project, site, building, body = create_ifc_project(spec)
    storeys = create_ifc_storeys(model, spec, building, body)
    walls = create_ifc_walls(model, spec, storeys, body)
    spaces = create_ifc_spaces(model, spec, storeys, body)
    doors = create_ifc_doors(model, spec, storeys, body)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    model.write(output_path)

    return {
        "path": output_path,
        "storeys": len(storeys),
        "walls": len(walls),
        "spaces": len(spaces),
        "doors": len(doors),
    }


def export_ifc_from_spec_file(spec_path, output_path):
    with open(spec_path, encoding="utf-8") as f:
        spec = json.load(f)
    return export_ifc(spec, output_path)
