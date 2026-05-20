# Lot Plotter QGIS Plugin

A QGIS plugin for plotting lot boundaries based on bearing and distance measurements, similar to the CAD PLOTTING TEMPLATE.xls spreadsheet.

## Features

- **Input bearings and distances** for each corner of a lot
- **Accepts azimuths or quadrant bearings** such as `45`, `N 45 30 E`, or `S 12-15-30 W`
- **Automatic coordinate calculation** using bearing/distance from a starting point
- **Area calculation** using the Shoelace formula
- **Closure error calculation** to verify lot closure accuracy
- **Closure ratio** (useful for checking survey quality)
- **AutoCAD PLINE script generation** for copy/paste drafting
- **Polygon visualization** on the QGIS map canvas
- **Export coordinates** to CSV file for further use

## Installation

1. The plugin is located in: `~/.local/share/QGIS/QGIS3/profiles/default/python/plugins/LotPlotter/`
2. Restart QGIS
3. Enable the plugin in **Plugins > Manage and Install Plugins** (search for "Lot Plotter")

## Usage

### Basic Workflow

1. **Open the Plugin**: Click the Lot Plotter icon in the toolbar or go to **Plugins > Lot Plotter > Lot Plotter**

2. **Set Starting Point**: 
   - Enter the X (Easting) and Y (Northing) coordinates of the starting point
   - Or select a tie point from the dropdown menus
   - The province dropdown loads tie point files from the plugin `LookUpData` folder, with GETools as a fallback
   - Default is (0, 0)

3. **Add Lot Corners**:
   - Click "Add Corner" to add a new row
   - Enter the **Bearing**
     - Decimal azimuth: `0`, `90`, `180`, `270`
     - Quadrant bearing: `N 45 30 E`, `S 12-15-30 W`
   - Enter the **Distance** (in the same units as your coordinates)

4. **Plot the Lot**:
   - Click "Plot Lot" to:
     - Calculate all corner coordinates
     - Compute the lot area
     - Calculate closure error
     - Create a polygon layer on the map

5. **View Results**:
   - Area in square units
   - Closure Error (distance from last point to first point)
   - Closure Ratio (1:ratio format - lower is better)
   - All corner coordinates

6. **Export Coordinates** (optional):
   - Click "Export Coordinates" to save corner coordinates to a CSV file

## Bearing Convention

The plugin uses standard surveying bearing notation:
- **0° or 360°** = North
- **90°** = East (clockwise from North)
- **180°** = South
- **270°** = West

## Coordinate Reference System

The plugin creates the lot layer using the current QGIS project CRS.

## Example

**Starting Point**: (500000, 2000000)

**Lot Corners**:
| Bearing | Distance |
|---------|----------|
| 45      | 100      |
| 135     | 100      |
| 225     | 100      |
| 315     | 100      |

This creates a square lot with corners at equal 90° angles.

## Closure Error Interpretation

- **0.00 units** = Perfect closure (rare in practice)
- **< 0.1 units** = Excellent survey
- **< 1 unit** = Good survey
- **> 1 unit** = Survey may need review

**Closure Ratio** is more useful for comparing different sized lots:
- Better ratios are typically **1:1000** or smaller
- **1:500** or larger = Less accurate

## Files Included

- `__init__.py` - Plugin loader
- `metadata.txt` - Plugin metadata
- `lot_plotter.py` - Main plugin code and dialog
- `lot_plotter_dialog.ui` - User interface definition
- `README.md` - This file

## Troubleshooting

### Plugin doesn't appear in QGIS
- Ensure the plugin folder is in the correct location
- Check QGIS plugin manager settings
- Restart QGIS after placing files

### "Invalid bearing or distance" error
- Ensure all values are numeric
- Bearing should be 0-360 degrees
- Distance should be a positive number

### Coordinates don't look right
- Verify starting point coordinates
- Check that bearings are in degrees (not radians)
- Ensure distance units match your coordinate system

## Future Enhancements

- Batch import of lot data from spreadsheets
- Adjustments for known survey errors
- Integration with traverse calculations

## License

This plugin is provided as-is for QGIS users.
