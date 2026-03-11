# FreeCAD MCP Guide

This guide explains how to set up and use the FreeCAD Model Context Protocol (MCP) server with `opencode`. It enables AI agents like `opencode` to directly interact with FreeCAD to create documents, modify objects, and run scripts.

## Prerequisites
1. **FreeCAD** installed on your system.
2. **Python** (3.12 or higher).
3. **opencode** installed and configured.
4. **uv** package manager installed (provides the `uvx` tool runner).
   - Install via pip: `pip install uv`

## 1. FreeCAD Addon Installation
You must install the FreeCAD MCP addon into your FreeCAD Mod directory.

1. Clone the repository:
   ```bash
   git clone https://github.com/neka-nat/freecad-mcp.git
   ```
2. Copy the `addon/FreeCADMCP` directory to your FreeCAD Mod directory:
   - **Windows:** `%APPDATA%\FreeCAD\Mod\`
   - **Mac:** `~/Library/Application Support/FreeCAD/Mod/`
   - **Linux:** `~/.FreeCAD/Mod/` or `~/snap/freecad/common/Mod/`
3. Restart FreeCAD.
4. Select **"MCP Addon"** from the Workbench dropdown list.
5. Click **"Start RPC Server"** in the FreeCAD MCP toolbar.

## 2. Setting Up opencode

Unlike Claude Desktop, `opencode` allows you to set up MCP servers locally per project.

Create an `opencode.json` file in your project root (e.g., `freecad-floorplan/opencode.json`) with the following content:

```json
{
  "mcp": {
    "freecad": {
      "type": "local",
      "command": ["uvx", "freecad-mcp"],
      "enabled": true
    }
  }
}
```

*Note: If you want to use text-only feedback to save AI tokens, change the command array to `["uvx", "freecad-mcp", "--only-text-feedback"]`.*

## 3. Verifying the Connection
Run the following command in your terminal to ensure `opencode` successfully connects to the FreeCAD MCP server:

```bash
opencode mcp list
```

You should see `freecad` listed with a `connected` status.

## 4. Available Capabilities
Once connected, `opencode` can perform the following actions inside FreeCAD:
- **`create_document`**: Create a new document.
- **`create_object`**: Create a new object (e.g., Part, Sketch).
- **`edit_object`**: Modify properties of an existing object.
- **`delete_object`**: Remove an object.
- **`execute_code`**: Execute arbitrary Python scripts within the FreeCAD environment.
- **`get_view`**: Retrieve a screenshot of the active view.
- **`get_objects` / `get_object`**: Read the structure and properties of document objects.
- **`insert_part_from_library`**: Insert standard parts from the FreeCAD library.
