import csv
import os
import math
import re
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QVariant
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField
from qgis.gui import QgisInterface

PLUGIN_DIR = os.path.dirname(__file__)
LOOKUP_DIR = os.path.join(PLUGIN_DIR, 'LookUpData')

FORM_CLASS, _ = uic.loadUiType(os.path.join(
    os.path.dirname(__file__), 'lot_plotter_dialog.ui'))


def parse_float_or_blank(value):
    try:
        text = str(value).strip()
        if text == "":
            return ""
        return f"{float(text):.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return ""


def parse_float(value):
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None


def parse_dms_angle(text):
    parts = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not parts:
        return None
    degrees = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 1 else 0.0
    seconds = float(parts[2]) if len(parts) > 2 else 0.0
    if minutes >= 60 or seconds >= 60:
        return None
    return degrees + minutes / 60.0 + seconds / 3600.0


def parse_bearing(value):
    text = str(value or "").strip().upper()
    if not text:
        return None

    compact = re.sub(r"[^NSEW0-9.]+", " ", text)
    quadrant = re.match(r"^\s*([NS])\s*(.*?)\s*([EW])\s*$", compact)
    if quadrant:
        ns, angle_text, ew = quadrant.groups()
        angle = parse_dms_angle(angle_text)
        if angle is None or angle > 90:
            return None
        if ns == "N" and ew == "E":
            return angle
        if ns == "S" and ew == "E":
            return 180.0 - angle
        if ns == "S" and ew == "W":
            return 180.0 + angle
        return (360.0 - angle) % 360.0

    angle = parse_dms_angle(text)
    if angle is None:
        return None
    return angle % 360.0


def load_provinces():
    path = os.path.join(LOOKUP_DIR, 'PrvDta.csv')
    provinces = []
    if not os.path.exists(path):
        return provinces
    with open(path, 'r', encoding='utf-8', errors='ignore', newline='') as handle:
        for row in csv.reader(handle):
            if len(row) >= 2 and row[0].strip():
                provinces.append({'code': row[0].strip(), 'name': row[1].strip()})
    return provinces


def load_tie_points_for_province(province_code):
    path = os.path.join(LOOKUP_DIR, f"{province_code}.csv")
    points = []
    if not os.path.exists(path):
        return points
    with open(path, 'r', encoding='utf-8-sig', errors='ignore', newline='') as handle:
        for row in csv.reader(handle):
            if len(row) < 12:
                continue
            marker = row[0].strip()
            number = row[1].strip()
            survey = row[2].strip()
            municipality = row[3].strip()
            province = row[4].strip()
            region = row[5].strip()
            lpcs_n = parse_float_or_blank(row[6] if len(row) > 6 else "")
            lpcs_e = parse_float_or_blank(row[7] if len(row) > 7 else "")
            prs_n = parse_float_or_blank(row[8] if len(row) > 8 else "")
            prs_e = parse_float_or_blank(row[9] if len(row) > 9 else "")
            ptm_n = parse_float_or_blank(row[10] if len(row) > 10 else "")
            ptm_e = parse_float_or_blank(row[11] if len(row) > 11 else "")
            point_name = " ".join(part for part in (marker, number) if part)
            description = " ".join(part for part in (marker, number, survey, municipality, province) if part)
            display = " | ".join(part for part in (municipality, point_name, survey) if part)
            points.append({
                'id': number,
                'description': description,
                'display': display,
                'point_name': point_name,
                'marker': marker,
                'survey': survey,
                'municipality': municipality,
                'province': province,
                'region': region,
                'lpcs_n': lpcs_n,
                'lpcs_e': lpcs_e,
                'prs_n': prs_n,
                'prs_e': prs_e,
                'ptm_n': ptm_n,
                'ptm_e': ptm_e,
            })
    return points


class TiePointChooserDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Choose Tie Point")
        self.resize(760, 420)
        self.provinces = load_provinces()
        self.tie_points = []

        layout = QtWidgets.QVBoxLayout(self)

        location_group = QtWidgets.QGroupBox("Tie Point")
        location_form = QtWidgets.QFormLayout(location_group)
        self.province_combo = QtWidgets.QComboBox()
        self.province_combo.setEditable(True)
        self.tie_point_combo = QtWidgets.QComboBox()
        self.tie_point_combo.setEditable(True)
        self.tie_point_combo.setMinimumContentsLength(70)
        self.tie_point_combo.setMaxVisibleItems(18)
        location_form.addRow("Province:", self.province_combo)
        location_form.addRow("Tie Point:", self.tie_point_combo)
        layout.addWidget(location_group)

        projection_group = QtWidgets.QGroupBox("Coordinate Source")
        projection_layout = QtWidgets.QHBoxLayout(projection_group)
        self.ptm_radio = QtWidgets.QRadioButton("PTM")
        self.prs_radio = QtWidgets.QRadioButton("PRS")
        self.lpcs_radio = QtWidgets.QRadioButton("LPCS")
        self.ptm_radio.setChecked(True)
        projection_layout.addWidget(self.ptm_radio)
        projection_layout.addWidget(self.prs_radio)
        projection_layout.addWidget(self.lpcs_radio)
        projection_layout.addStretch()
        layout.addWidget(projection_group)

        coord_group = QtWidgets.QGroupBox("Coordinates")
        coord_form = QtWidgets.QFormLayout(coord_group)
        self.tp_id_edit = QtWidgets.QLineEdit()
        self.municipality_edit = QtWidgets.QLineEdit()
        self.survey_edit = QtWidgets.QLineEdit()
        self.northing_edit = QtWidgets.QLineEdit()
        self.easting_edit = QtWidgets.QLineEdit()
        for edit in (
            self.tp_id_edit,
            self.municipality_edit,
            self.survey_edit,
            self.northing_edit,
            self.easting_edit,
        ):
            edit.setReadOnly(True)
        coord_form.addRow("TP Id:", self.tp_id_edit)
        coord_form.addRow("Municipality:", self.municipality_edit)
        coord_form.addRow("Survey:", self.survey_edit)
        coord_form.addRow("Northing:", self.northing_edit)
        coord_form.addRow("Easting:", self.easting_edit)
        layout.addWidget(coord_group)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.province_combo.currentIndexChanged.connect(self.populate_tie_points)
        self.tie_point_combo.currentIndexChanged.connect(self.refresh_selected_point)
        self.ptm_radio.toggled.connect(self.refresh_selected_point)
        self.prs_radio.toggled.connect(self.refresh_selected_point)
        self.lpcs_radio.toggled.connect(self.refresh_selected_point)

        self.populate_provinces()

    def populate_provinces(self):
        self.province_combo.blockSignals(True)
        self.province_combo.clear()
        for province in self.provinces:
            self.province_combo.addItem(f"{province['code']} - {province['name']}", province)
        self.province_combo.blockSignals(False)
        self.populate_tie_points()

    def populate_tie_points(self):
        province = self.province_combo.currentData() or {}
        self.tie_points = load_tie_points_for_province(province.get('code', ''))
        self.tie_point_combo.blockSignals(True)
        self.tie_point_combo.clear()
        for point in self.tie_points:
            self.tie_point_combo.addItem(point.get('display', point.get('description', '')), point)
        self.tie_point_combo.blockSignals(False)
        self.refresh_selected_point()

    def selected_projection(self):
        if self.prs_radio.isChecked():
            return 'prs'
        if self.lpcs_radio.isChecked():
            return 'lpcs'
        return 'ptm'

    def refresh_selected_point(self):
        point = self.tie_point_combo.currentData() or {}
        projection = self.selected_projection()
        self.tp_id_edit.setText(point.get('id', ''))
        self.municipality_edit.setText(point.get('municipality', ''))
        self.survey_edit.setText(point.get('survey', ''))
        self.northing_edit.setText(point.get(f'{projection}_n', ''))
        self.easting_edit.setText(point.get(f'{projection}_e', ''))

    def selected_values(self):
        point = self.tie_point_combo.currentData() or {}
        projection = self.selected_projection()
        return {
            'point': point,
            'projection': projection.upper(),
            'northing': point.get(f'{projection}_n', ''),
            'easting': point.get(f'{projection}_e', ''),
            'description': point.get('description', self.tie_point_combo.currentText()),
        }


class LotPlotterDialog(QtWidgets.QDialog, FORM_CLASS):
    def __init__(self, parent=None):
        super(LotPlotterDialog, self).__init__(parent)
        self.setupUi(self)
        self.iface = None
        self.bearings = []
        self.distances = []
        self.calculated_coordinates = []
        self.provinces = []
        self.tie_points = []
        self.autocad_script = ""
        
        # Connect buttons
        self.add_corner_btn.clicked.connect(self.add_corner)
        self.remove_corner_btn.clicked.connect(self.remove_corner)
        self.plot_btn.clicked.connect(self.plot_lot)
        self.clear_btn.clicked.connect(self.clear_all)
        self.export_btn.clicked.connect(self.export_coordinates)
        self.province_combo.currentIndexChanged.connect(self.on_province_changed)
        self.tie_point_combo.currentIndexChanged.connect(self.on_tie_point_changed)
        try:
            self.choose_tie_btn.clicked.connect(self.open_tie_point_dialog)
        except Exception:
            pass
        self.populate_provinces()
        for _ in range(4):
            self.add_corner()
        
    def add_corner(self):
        """Add a new corner row to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.table.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(row + 1)))
        
    def remove_corner(self):
        """Remove selected corner row"""
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.refresh_corner_numbers()
    
    def clear_all(self):
        """Clear all corners"""
        self.table.setRowCount(0)
        self.results_text.clear()
        self.calculated_coordinates = []
        self.autocad_script = ""
        for _ in range(4):
            self.add_corner()

    def refresh_corner_numbers(self):
        for row in range(self.table.rowCount()):
            self.table.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(row + 1)))
        
    def populate_provinces(self):
        self.provinces = load_provinces()
        self.province_combo.clear()
        self.tie_point_combo.clear()
        self.tie_points = []
        self.province_combo.setEditable(True)
        self.tie_point_combo.setEditable(True)
        
        for province in self.provinces:
            self.province_combo.addItem(f"{province['code']} - {province['name']}", province['code'])
        
        if self.provinces:
            self.province_combo.setCurrentIndex(0)
            self.on_province_changed(0)
        
    def on_province_changed(self, index):
        if index < 0 or index >= len(self.provinces):
            self.tie_point_combo.clear()
            self.tie_points = []
            return
        province_code = self.provinces[index]['code']
        self.tie_points = load_tie_points_for_province(province_code)
        self.tie_point_combo.clear()
        self.tie_point_combo.addItem("Select a tie point", None)
        for point in self.tie_points:
            self.tie_point_combo.addItem(point['display'], point)
        
    def on_tie_point_changed(self, index):
        if index <= 0 or index > len(self.tie_points):
            return
        point = self.tie_point_combo.itemData(index)
        if not point:
            return
        coords = self.select_tie_point_coordinates(point)
        if coords is not None:
            x, y = coords
            self.start_x_input.setText(f"{x:.3f}")
            self.start_y_input.setText(f"{y:.3f}")
            self.results_text.setText(
                f"Selected tie point: {point['display']}\nCoordinates set to: ({x:.3f}, {y:.3f})")
        else:
            QtWidgets.QMessageBox.warning(self, "Tie Point Data", 
                "Selected tie point does not contain usable coordinates.")

    def select_tie_point_coordinates(self, point):
        for x_key, y_key in [('ptm_e', 'ptm_n'), ('prs_e', 'prs_n'), ('lpcs_e', 'lpcs_n')]:
            x = parse_float(point.get(x_key))
            y = parse_float(point.get(y_key))
            if x is not None and y is not None:
                return x, y
        return None

    def open_tie_point_dialog(self):
        dlg = TiePointChooserDialog(self)
        if dlg.exec_() == QtWidgets.QDialog.Accepted:
            values = dlg.selected_values()
            x = parse_float(values.get('easting'))
            y = parse_float(values.get('northing'))
            if x is None or y is None:
                QtWidgets.QMessageBox.warning(
                    self,
                    "Tie Point Data",
                    "Selected tie point does not contain usable numeric coordinates for that coordinate source.",
                )
                return
            self.start_x_input.setText(f"{x:.3f}")
            self.start_y_input.setText(f"{y:.3f}")
            self.results_text.setText(
                f"Selected tie point: {values.get('description', '')}\n"
                f"Coordinate source: {values.get('projection', '')}\n"
                f"Coordinates set to: ({x:.3f}, {y:.3f})"
            )
        
    def get_corners_from_table(self):
        """Extract bearing/distance data from table"""
        corners = []
        for row in range(self.table.rowCount()):
            try:
                bearing_item = self.table.item(row, 0)
                distance_item = self.table.item(row, 1)
                
                if bearing_item and distance_item:
                    bearing_text = bearing_item.text().strip()
                    distance = parse_float(distance_item.text())
                    bearing = parse_bearing(bearing_text)
                    if bearing is None or distance is None or distance <= 0:
                        raise ValueError
                    corners.append({'bearing': bearing, 'bearing_text': bearing_text, 'distance': distance})
            except ValueError:
                QtWidgets.QMessageBox.warning(self, "Input Error", 
                    f"Row {row + 1}: Invalid bearing or distance value.\n\n"
                    "Bearing can be an azimuth like 45 or a quadrant bearing like N 45 30 E.")
                return None
        return corners
    
    def plot_lot(self):
        """Calculate lot coordinates and plot on map"""
        try:
            # Get input values
            start_x = parse_float(self.start_x_input.text())
            start_y = parse_float(self.start_y_input.text())
            if start_x is None or start_y is None:
                raise ValueError("Starting X and Y coordinates must be numeric.")
            corners = self.get_corners_from_table()
            
            if not corners or len(corners) < 3:
                QtWidgets.QMessageBox.warning(self, "Input Error", 
                    "Please enter at least 3 corners")
                return
                
            # Calculate coordinates
            coordinates = self.calculate_coordinates(start_x, start_y, corners)
            self.calculated_coordinates = coordinates  # Store for export
            self.autocad_script = self.generate_autocad_script(coordinates)
            area = self.calculate_area(coordinates)
            closure_error = self.calculate_closure_error(coordinates)
            
            # Display results with coordinates
            results = f"=== LOT PLOTTER RESULTS ===\n\n"
            results += f"Starting Point: ({start_x:.2f}, {start_y:.2f})\n\n"
            results += f"Traverse Lines:\n"
            for i, corner in enumerate(corners, start=1):
                results += (
                    f"  Line {i}: {corner['bearing_text']} "
                    f"(azimuth {corner['bearing']:.6f})  {corner['distance']:.3f}\n"
                )
            results += "\n"
            results += f"Corner Coordinates:\n"
            for i, (x, y) in enumerate(coordinates):
                results += f"  Corner {i}: ({x:.2f}, {y:.2f})\n"
            results += f"\n=== CALCULATIONS ===\n"
            results += f"Area: {area:.2f} sq units\n"
            results += f"Closure Error: {closure_error:.4f} units\n"
            results += f"Number of corners: {len(corners)}\n"
            
            # Closure ratio (acceptable usually < 1:1000)
            perimeter = self.calculate_perimeter(coordinates)
            if perimeter > 0 and closure_error > 0:
                results += f"Closure Ratio: 1:{perimeter/closure_error:.0f}\n"
            elif perimeter > 0:
                results += "Closure Ratio: Perfect closure\n"
            results += f"Perimeter: {perimeter:.2f} units\n"
            results += "\n=== AUTOCAD PLINE SCRIPT ===\n"
            results += self.autocad_script
            
            self.results_text.setText(results)
            
            # Create and add layer to map
            self.create_lot_layer(coordinates)
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"Lot plotted successfully!\nArea: {area:.2f} sq units\nClosure Error: {closure_error:.4f}")
                
        except ValueError as e:
            QtWidgets.QMessageBox.critical(self, "Error", f"Invalid input: {str(e)}")
    
    def calculate_coordinates(self, start_x, start_y, corners):
        """Calculate coordinates for each corner based on bearing and distance"""
        coordinates = [(start_x, start_y)]
        x, y = start_x, start_y
        
        for corner in corners:
            bearing = corner['bearing']  # Bearing in degrees (0-360)
            distance = corner['distance']
            
            # Convert bearing to radians (bearing is measured clockwise from North)
            # In standard math, 0 is East and increases counter-clockwise
            # Bearing: 0 = North, 90 = East, 180 = South, 270 = West
            angle_rad = math.radians(90 - bearing)  # Convert to standard math angle
            
            x += distance * math.cos(angle_rad)
            y += distance * math.sin(angle_rad)
            
            coordinates.append((x, y))
        
        return coordinates

    def generate_autocad_script(self, coordinates):
        lines = ["PLINE"]
        for x, y in coordinates:
            lines.append(f"{x:.3f},{y:.3f}")
        lines.append("C")
        return "\n".join(lines)
    
    def calculate_area(self, coordinates):
        """Calculate area using Shoelace formula"""
        n = len(coordinates)
        if n < 3:
            return 0
        
        area = 0
        for i in range(n):
            x1, y1 = coordinates[i]
            x2, y2 = coordinates[(i + 1) % n]
            area += x1 * y2 - x2 * y1
        
        return abs(area) / 2
    
    def calculate_closure_error(self, coordinates):
        """Calculate closure error (distance from last point to first point)"""
        if len(coordinates) < 2:
            return 0
        
        last_x, last_y = coordinates[-1]
        first_x, first_y = coordinates[0]
        
        error = math.sqrt((last_x - first_x)**2 + (last_y - first_y)**2)
        return error
    
    def calculate_perimeter(self, coordinates):
        """Calculate perimeter of the lot"""
        if len(coordinates) < 2:
            return 0
        
        perimeter = 0
        for i in range(len(coordinates) - 1):
            x1, y1 = coordinates[i]
            x2, y2 = coordinates[i + 1]
            distance = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            perimeter += distance
        
        # Add distance from last to first point
        last_x, last_y = coordinates[-1]
        first_x, first_y = coordinates[0]
        distance = math.sqrt((first_x - last_x)**2 + (first_y - last_y)**2)
        perimeter += distance
        
        return perimeter
    
    def export_coordinates(self):
        """Export calculated coordinates to CSV file"""
        if not self.calculated_coordinates:
            QtWidgets.QMessageBox.warning(self, "No Data", 
                "Please plot a lot first before exporting")
            return
        
        file_path, _ = QFileDialog.getSaveFileName(
            self, "Export Coordinates", "", "CSV Files (*.csv)")
        
        if file_path:
            try:
                with open(file_path, 'w') as f:
                    f.write("Corner_Number,X,Y\n")
                    for i, (x, y) in enumerate(self.calculated_coordinates):
                        f.write(f"{i},{x:.4f},{y:.4f}\n")
                
                QtWidgets.QMessageBox.information(self, "Success", 
                    f"Coordinates exported to:\n{file_path}")
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Error", 
                    f"Failed to export: {str(e)}")
    
    def create_lot_layer(self, coordinates):
        """Create a vector layer and add the lot polygon"""
        if not self.iface:
            return
        
        project_crs = QgsProject.instance().crs()
        crs_authid = project_crs.authid() if project_crs and project_crs.isValid() else "EPSG:4326"
        layer = QgsVectorLayer(f"Polygon?crs={crs_authid}", "Lot Boundary", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("lot_id", QVariant.String),
            QgsField("area", QVariant.Double),
            QgsField("perimeter", QVariant.Double),
            QgsField("closure", QVariant.Double),
            QgsField("corners", QVariant.Int),
        ])
        layer.updateFields()
        
        # Create feature with polygon geometry
        points = [QgsPointXY(x, y) for x, y in coordinates]
        points.append(QgsPointXY(coordinates[0][0], coordinates[0][1]))  # Close polygon
        
        feature = QgsFeature()
        geometry = QgsGeometry.fromPolygonXY([points])
        feature.setGeometry(geometry)
        feature.setAttributes([
            "Lot 1",
            geometry.area(),
            geometry.length(),
            self.calculate_closure_error(coordinates),
            max(len(coordinates) - 1, 0),
        ])
        provider.addFeatures([feature])
        layer.updateExtents()
        
        # Add layer to map
        QgsProject.instance().addMapLayer(layer)
        
        # Zoom to layer
        self.iface.mapCanvas().zoomToFeatureExtent(layer.extent())
        self.iface.mapCanvas().refresh()


class LotPlotter:
    def __init__(self, iface):
        self.iface = iface
        self.action = None
        self.dialog = None
        
    def initGui(self):
        """Initialize the GUI"""
        from qgis.PyQt.QtGui import QIcon
        
        icon_path = os.path.join(os.path.dirname(__file__), 'icon.png')
        icon = QIcon(icon_path) if os.path.exists(icon_path) else QIcon()
        
        self.action = QtWidgets.QAction(icon, 'Lot Plotter', self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu('&Lot Plotter', self.action)
    
    def unload(self):
        """Remove the plugin menu item and toolbar icon"""
        self.iface.removePluginMenu('&Lot Plotter', self.action)
        self.iface.removeToolBarIcon(self.action)
    
    def run(self):
        """Execute the plugin"""
        if not self.dialog:
            self.dialog = LotPlotterDialog(self.iface.mainWindow())
            self.dialog.iface = self.iface
        
        self.dialog.show()
