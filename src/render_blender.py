#!/usr/bin/env python3
"""
render_blender.py
=================
Headless Cycles render of the tubehouse Blender scene.

Usage
-----
  blender --background output/blend/tubehouse_scene.blend \
      --python src/render_blender.py

Configuration is read from spec/blender_materials.json (render section).
"""

import json
import os
import sys

SCRIPT_DIR = (
    os.path.dirname(os.path.abspath(__file__))
    if "__file__" in dir()
    else os.path.dirname(os.path.abspath(sys.argv[0]))
)
PROJECT_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, os.pardir))

SPEC_FILE = os.path.join(PROJECT_DIR, "spec", "blender_materials.json")
DEFAULT_OUTPUT = os.path.join(PROJECT_DIR, "output", "png", "tubehouse_blender_render.png")

try:
    import bpy
except ImportError:
    bpy = None


def load_render_config():
    """Load render settings from the JSON sidecar."""
    if not os.path.isfile(SPEC_FILE):
        return {}
    with open(SPEC_FILE, encoding="utf-8") as fh:
        return json.load(fh).get("render", {})


def configure_cycles(scene, config):
    """Configure Cycles render settings on the scene."""
    scene.render.engine = "CYCLES"
    cycles = scene.cycles

    samples = config.get("samples", 128)
    cycles.samples = samples
    cycles.preview_samples = min(samples, 32)

    cpu_threads = config.get("cpu_threads", 0)
    if cpu_threads > 0:
        cycles.thread_mode = "FIXED"
        cycles.threads = cpu_threads
    else:
        cycles.thread_mode = "AUTO"

    cycles.feature_set = "SUPPORTED"
    if hasattr(cycles, "debug_bvh_type"):
        cycles.debug_bvh_type = "DYNAMIC_BVH"
    cycles.debug_use_spatial_splits = True

    print(f"  Cycles configured: {samples} samples, thread_mode={cycles.thread_mode}")


def configure_resolution(scene, config):
    """Set render resolution."""
    scene.render.resolution_x = config.get("resolution_x", 1920)
    scene.render.resolution_y = config.get("resolution_y", 1080)
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0


def configure_output(scene, output_path):
    """Set the output file path and format."""
    scene.render.filepath = output_path
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.image_settings.compression = 90


def main():
    """Entry point: configure and render the scene."""
    print(f"\n{'=' * 60}")
    print("render_blender: Cycles headless render")
    print(f"{'=' * 60}")

    if bpy is None:
        print("ERROR: This script must be run inside Blender.")
        print("  Usage: blender --background scene.blend --python src/render_blender.py")
        return False

    config = load_render_config()
    scene = bpy.context.scene

    print("  Configuring Cycles...")
    configure_cycles(scene, config)
    configure_resolution(scene, config)

    output_path = os.environ.get("TUBEHOUSE_RENDER", DEFAULT_OUTPUT)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    configure_output(scene, output_path)

    print(f"  Rendering to: {output_path}")
    print(f"  Resolution: {scene.render.resolution_x}x{scene.render.resolution_y}")
    print(f"  Samples: {scene.cycles.samples}")
    print("  Rendering (this may take a few minutes)...")

    bpy.ops.render.render(write_still=True)

    print(f"  Render complete: {output_path}")
    return True


if __name__ == "__main__":
    main()