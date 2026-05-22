# Lot Plotter QGIS Plugin

A QGIS plugin for plotting lot boundaries based on bearing and distance measurements, following the format in land titles and lot description. A tool under The Atlas Project.

## Features

- **Input bearings and distances** for each corner of a lot
- **Accepts azimuths or quadrant bearings** such as `45`, `N45D30E`, or `S12D15W`
- **Automatic coordinate calculation** using bearing/distance from a starting point
- **Area calculation** using the Shoelace formula
- **Closure error calculation** to verify lot closure accuracy
- **Closure ratio** (useful for checking survey quality)
- **AutoCAD PLINE script generation** for copy/paste drafting
- **Polygon visualization** on the QGIS map canvas
- **Export coordinates** to CSV file for further use

## Usage

### Basic Workflow

1. **Open the Plugin**: Click the Lot Plotter icon in the toolbar or go to **Plugins > Lot Plotter > Lot Plotter**

2. **Set Starting Point**: 
   - Enter the X (Easting) and Y (Northing) coordinates of the starting point
   - Or click "Choose Tie-Point..." and select a tie point from the lookup data
   - If PTM is selected, the plotted lot layer uses Luzon 1911 / Philippines CRS, with the zone assigned from the selected tie point province
   - If PRS is selected, the plotted lot layer uses PRS92 / Philippines CRS with the same province-based zone assignment
   - If LPCS is selected, the plotted lot layer is created with unknown CRS because LPCS is a local floating coordinate system
   - Default is (0, 0)

3. **Fill Lot / Claimant Details**:
   - Click "Lot Details..." to open the lot/claimant details window
   - Lot ID is generated automatically
   - Enter lot name/number, GE/surveyor, survey number/date, claimant, and survey type
   - Selected tie point name/northing/easting are stored as generated layer fields

4. **Add Lot Corners**:
   - Enter the number of lot corners; the line table adjusts automatically
   - The table includes a line guide such as `TP-1`, `1-2`, `2-3`, and `4-1`
   - The `TP-1` row is used only to locate corner 1 from the tie point; it is not drawn as part of the final polygon
   - Click "Add Corner" to add another line row
   - Or copy bearing/distance rows from a spreadsheet and press Ctrl+V in the table
   - Enter the **Bearing**
     - Quadrant bearing: `N45D30E`, `S12D15W`
     - Decimal azimuth: `45`, `90`, `180`
   - Enter the **Distance** (in the same units as your coordinates)

5. **Plot the Lot**:
   - Click "Plot Lot" to:
     - Calculate all corner coordinates
     - Compute the lot area
     - Calculate closure error
     - Create a polygon layer on the map

6. **View Results**:
   - Area in square units
   - Closure Error (distance from last point to first point)
   - Closure Ratio (1:ratio format - lower is better)
   - All corner coordinates
   - A live sketch of the lot boundary updates as bearings and distances are typed

7. **Export Coordinates** (optional):
   - Click "Export Coordinates" to save corner coordinates to a CSV file

## Coordinate Reference System

The plugin creates the lot layer using the current QGIS project CRS unless a selected tie point defines the coordinate source. PTM tie points assign Luzon 1911 / Philippines Zone I-V, and PRS tie points assign PRS92 / Philippines Zone I-V, based on the selected province. LPCS tie points create an unknown-CRS layer because those coordinates are local/floating and should not be treated as georeferenced EPSG coordinates.

## Closure Error Interpretation

- **0.00 units** = Perfect closure (rare in practice)
- **< 0.1 units** = Excellent survey
- **< 1 unit** = Good survey
- **> 1 unit** = Survey may need review

**Closure Ratio** is more useful for comparing different sized lots:
- Better ratios are typically **1:1000** or smaller
- **1:500** or larger = Less accurate

## Troubleshooting

### Plugin doesn't appear in QGIS
- Ensure the plugin folder is in the correct location
- Check QGIS plugin manager settings
- Restart QGIS after placing files

### "Invalid bearing or distance" error
- Ensure distance values are numeric
- Bearing can be a decimal azimuth (`45`) or quadrant bearing (`N45D30E`)
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

This plugin is licensed under GPL-2.0-or-later. See the `LICENSE` file.
