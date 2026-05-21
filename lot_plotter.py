import csv
import json
import os
import math
import re
from qgis.PyQt import QtWidgets, uic
from qgis.PyQt.QtWidgets import QFileDialog
from qgis.PyQt.QtCore import QEvent, QSettings, Qt, QVariant
from qgis.PyQt.QtGui import QBrush, QColor, QFont, QKeySequence, QPen
from qgis.core import QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField
from qgis.gui import QgisInterface

PLUGIN_DIR = os.path.dirname(__file__)
LOOKUP_DIR = os.path.join(PLUGIN_DIR, 'LookUpData')
SETTINGS_KEY = 'LotPlotter/last_state'
SURVEY_TYPES = [
    'CADASTRAL',
    'SUBDIVISION',
    'CONSOLIDATION',
    'CONSOLIDATION-SUBDIVISION',
    'RELOCATION',
    'SKETCH PLAN',
    'SPECIAL WORK ORDER',
    'OTHER',
]
ISLAND_GROUPS = ['LUZON', 'VISAYAS', 'MINDANAO']
PROVINCE_ISLANDS = {
    'ABRA': 'LUZON', 'APAYAO': 'LUZON', 'BENGUET': 'LUZON', 'IFUGAO': 'LUZON',
    'KALINGA': 'LUZON', 'MOUNTAIN PROVINCE': 'LUZON', 'ILOCOS NORTE': 'LUZON',
    'ILOCOS SUR': 'LUZON', 'LA UNION': 'LUZON', 'PANGASINAN': 'LUZON',
    'BATANES': 'LUZON', 'CAGAYAN': 'LUZON', 'ISABELA': 'LUZON',
    'NUEVA VIZCAYA': 'LUZON', 'QUIRINO': 'LUZON', 'BATAAN': 'LUZON',
    'BULACAN': 'LUZON', 'NUEVA ECIJA': 'LUZON', 'PAMPANGA': 'LUZON',
    'TARLAC': 'LUZON', 'ZAMBALES': 'LUZON', 'AURORA': 'LUZON',
    'BATANGAS': 'LUZON', 'CAVITE': 'LUZON', 'LAGUNA': 'LUZON',
    'QUEZON': 'LUZON', 'RIZAL': 'LUZON', 'METRO MANILA': 'LUZON',
    'NATIONAL CAPITAL REGION': 'LUZON', 'NCR': 'LUZON', 'ALBAY': 'LUZON',
    'CAMARINES NORTE': 'LUZON', 'CAMARINES SUR': 'LUZON',
    'CATANDUANES': 'LUZON', 'MASBATE': 'LUZON', 'SORSOGON': 'LUZON',
    'MARINDUQUE': 'LUZON', 'OCCIDENTAL MINDORO': 'LUZON',
    'ORIENTAL MINDORO': 'LUZON', 'PALAWAN': 'LUZON', 'ROMBLON': 'LUZON',
    'AKLAN': 'VISAYAS', 'ANTIQUE': 'VISAYAS', 'CAPIZ': 'VISAYAS',
    'ILOILO': 'VISAYAS', 'ILO-ILO': 'VISAYAS', 'NEGROS OCCIDENTAL': 'VISAYAS',
    'GUIMARAS': 'VISAYAS', 'BOHOL': 'VISAYAS', 'CEBU': 'VISAYAS',
    'NEGROS ORIENTAL': 'VISAYAS', 'SIQUIJOR': 'VISAYAS',
    'EASTERN SAMAR': 'VISAYAS', 'LEYTE': 'VISAYAS',
    'NORTHERN SAMAR': 'VISAYAS', 'SAMAR': 'VISAYAS',
    'WESTERN SAMAR': 'VISAYAS', 'SOUTHERN LEYTE': 'VISAYAS',
    'BILIRAN': 'VISAYAS',
    'ZAMBOANGA DEL NORTE': 'MINDANAO', 'ZAMBOANGA DEL SUR': 'MINDANAO',
    'ZAMBOANGA SIBUGAY': 'MINDANAO', 'BUKIDNON': 'MINDANAO',
    'CAMIGUIN': 'MINDANAO', 'LANAO DEL NORTE': 'MINDANAO',
    'MISAMIS OCCIDENTAL': 'MINDANAO', 'MISAMIS ORIENTAL': 'MINDANAO',
    'COMPOSTELA VALLEY': 'MINDANAO', 'DAVAO DE ORO': 'MINDANAO',
    'DAVAO DEL NORTE': 'MINDANAO', 'DAVAO DEL SUR': 'MINDANAO',
    'DAVAO ORIENTAL': 'MINDANAO', 'NORTH COTABATO': 'MINDANAO',
    'COTABATO': 'MINDANAO', 'SARANGANI': 'MINDANAO',
    'SOUTH COTABATO': 'MINDANAO', 'SULTAN KUDARAT': 'MINDANAO',
    'AGUSAN DEL NORTE': 'MINDANAO', 'AGUSAN DEL SUR': 'MINDANAO',
    'DINAGAT ISLANDS': 'MINDANAO', 'SURIGAO DEL NORTE': 'MINDANAO',
    'SURIGAO DEL SUR': 'MINDANAO', 'BASILAN': 'MINDANAO',
    'LANAO DEL SUR': 'MINDANAO', 'MAGUINDANAO': 'MINDANAO',
    'TAWI-TAWI': 'MINDANAO', 'TAWI TAWI': 'MINDANAO', 'SULU': 'MINDANAO',
}
LUZON_1911_ZONE_CRS = {
    'I': ('Zone I', 'EPSG:25391'),
    'II': ('Zone II', 'EPSG:25392'),
    'III': ('Zone III', 'EPSG:25393'),
    'IV': ('Zone IV', 'EPSG:25394'),
    'V': ('Zone V', 'EPSG:25395'),
}
PRS92_ZONE_CRS = {
    'I': ('Zone I', 'EPSG:3121'),
    'II': ('Zone II', 'EPSG:3122'),
    'III': ('Zone III', 'EPSG:3123'),
    'IV': ('Zone IV', 'EPSG:3124'),
    'V': ('Zone V', 'EPSG:3125'),
}
PTM_PROVINCE_ZONES = {
    'ABRA': 'III',
    'BENGUET': 'III',
    'IFUGAO': 'III',
    'MOUNTAIN PROVINCE': 'III',
    'KALINGA': 'III',
    'APAYAO': 'III',
    'METRO MANILA': 'III',
    'NATIONAL CAPITAL REGION': 'III',
    'NCR': 'III',
    'ILOCOS NORTE': 'III',
    'ILOCOS SUR': 'III',
    'LA UNION': 'III',
    'PANGASINAN': 'III',
    'BATANES': 'III',
    'CAGAYAN': 'III',
    'NUEVA VIZCAYA': 'III',
    'QUIRINO': 'III',
    'BATAAN': 'III',
    'BULACAN': 'III',
    'NUEVA ECIJA': 'III',
    'PAMPANGA': 'III',
    'TARLAC': 'III',
    'ZAMBALES': 'III',
    'AURORA': 'III',
    'BATANGAS': 'III',
    'CAVITE': 'III',
    'LAGUNA': 'III',
    'MARINDUQUE': 'III',
    'OCCIDENTAL MINDORO': 'III',
    'ORIENTAL MINDORO': 'III',
    'RIZAL': 'III',
    'PALAWAN': 'I',
    'ROMBLON': 'IV',
    'ALBAY': 'IV',
    'CAMARINES NORTE': 'IV',
    'CAMARINES SUR': 'IV',
    'CATANDUANES': 'IV',
    'MASBATE': 'IV',
    'SORSOGON': 'IV',
    'AKLAN': 'IV',
    'ANTIQUE': 'IV',
    'CAPIZ': 'IV',
    'ILOILO': 'IV',
    'ILO-ILO': 'IV',
    'NEGROS OCCIDENTAL': 'IV',
    'GUIMARAS': 'IV',
    'BOHOL': 'V',
    'CEBU': 'IV',
    'NEGROS ORIENTAL': 'V',
    'SIQUIJOR': 'V',
    'EASTERN SAMAR': 'V',
    'LEYTE': 'V',
    'NORTHERN SAMAR': 'V',
    'SAMAR': 'V',
    'WESTERN SAMAR': 'V',
    'SOUTHERN LEYTE': 'V',
    'BILIRAN': 'V',
    'ZAMBOANGA DEL NORTE': 'IV',
    'ZAMBOANGA DEL SUR': 'IV',
    'ZAMBOANGA SIBUGAY': 'IV',
    'BUKIDNON': 'V',
    'CAMIGUIN': 'V',
    'LANAO DEL NORTE': 'V',
    'MISAMIS OCCIDENTAL': 'IV',
    'MISAMIS ORIENTAL': 'V',
    'COMPOSTELA VALLEY': 'V',
    'DAVAO DE ORO': 'V',
    'DAVAO DEL NORTE': 'V',
    'DAVAO DEL SUR': 'V',
    'DAVAO ORIENTAL': 'V',
    'NORTH COTABATO': 'V',
    'COTABATO': 'V',
    'SARANGANI': 'V',
    'SOUTH COTABATO': 'V',
    'SULTAN KUDARAT': 'V',
    'AGUSAN DEL NORTE': 'V',
    'AGUSAN DEL SUR': 'V',
    'DINAGAT ISLANDS': 'V',
    'SURIGAO DEL NORTE': 'V',
    'SURIGAO DEL SUR': 'V',
    'BASILAN': 'IV',
    'LANAO DEL SUR': 'V',
    'MAGUINDANAO': 'V',
    'TAWI-TAWI': 'III',
    'TAWI TAWI': 'III',
    'SULU': 'III',
}

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


def read_dollar_lookup_rows(prefix):
    rows = []
    for extension in ('Txt', 'Dta', 'csv'):
        for name in os.listdir(LOOKUP_DIR):
            if not name.lower().startswith(prefix.lower()) or not name.lower().endswith(f'.{extension.lower()}'):
                continue
            path = os.path.join(LOOKUP_DIR, name)
            with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
                for line in handle:
                    parts = [part.strip() for part in line.strip().split('$')]
                    if len(parts) >= 2 and parts[0] and parts[1]:
                        rows.append({'code': parts[0], 'name': parts[1]})
    seen = set()
    unique = []
    for row in rows:
        if row['code'] in seen:
            continue
        seen.add(row['code'])
        unique.append(row)
    return unique


def load_municipalities_for_province(province_code):
    rows = read_dollar_lookup_rows('MunDta')
    return [row for row in rows if row['code'].startswith(str(province_code))]


def load_barangays_for_municipality(municipality_code):
    rows = read_dollar_lookup_rows('BgyDta')
    return [row for row in rows if row['code'].startswith(str(municipality_code))]


def load_simple_lookup_values(file_name, fallback):
    path = os.path.join(LOOKUP_DIR, file_name)
    values = []
    if os.path.exists(path):
        with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
            for row in csv.reader(handle):
                if row and row[0].strip():
                    values.append(row[0].strip())
    return values or fallback


def parse_dms_angle(text):
    parts = re.findall(r"\d+(?:\.\d+)?", str(text))
    if not parts:
        return None
    degrees = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 1 else 0.0
    seconds = float(parts[2]) if len(parts) > 2 else 0.0
    if degrees > 180 or minutes >= 60 or seconds >= 60:
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


def normalize_lookup_name(value):
    text = re.sub(r"[^A-Z0-9]+", " ", str(value or "").upper()).strip()
    return re.sub(r"\s+", " ", text)


def parse_longitude(value):
    text = str(value or "").strip()
    if not text:
        return None
    sign = -1 if text.upper().startswith("W") else 1
    parts = re.findall(r"\d+(?:\.\d+)?", text)
    if not parts:
        return None
    degrees = float(parts[0])
    minutes = float(parts[1]) if len(parts) > 1 else 0.0
    seconds = float(parts[2]) if len(parts) > 2 else 0.0
    if minutes >= 60 or seconds >= 60:
        return None
    return sign * (degrees + minutes / 60.0 + seconds / 3600.0)


def ptm_zone_for_point(point):
    province = normalize_lookup_name(point.get('province', ''))
    municipality = normalize_lookup_name(point.get('municipality', ''))
    longitude = parse_longitude(point.get('longitude', ''))

    if 'CAMOTES' in municipality:
        return 'V'
    if province in ('ISABELA', 'QUEZON') and longitude is not None:
        return 'IV' if longitude >= 122 else 'III'
    if province == 'ISABELA':
        return 'III'
    if province == 'QUEZON':
        return 'III'
    if province in PTM_PROVINCE_ZONES:
        return PTM_PROVINCE_ZONES[province]
    for mapped_province, zone_code in PTM_PROVINCE_ZONES.items():
        if mapped_province in province or province in mapped_province:
            return zone_code
    return None


def crs_for_tie_point(values):
    projection = values.get('projection')
    if projection == 'LPCS':
        return {
            'authid': '',
            'zone': 'Unknown / Local Floating Coordinates',
            'label': 'Unknown CRS (LPCS)',
            'force_unknown': True,
        }
    if projection not in ('PTM', 'PRS'):
        return {'authid': None, 'zone': '', 'label': '', 'force_unknown': False}

    zone_code = ptm_zone_for_point(values.get('point') or {})
    if not zone_code:
        return {'authid': None, 'zone': '', 'label': '', 'force_unknown': False}

    if projection == 'PRS':
        zone_name, authid = PRS92_ZONE_CRS[zone_code]
        label = f"PRS92 / Philippines {zone_name}"
    else:
        zone_name, authid = LUZON_1911_ZONE_CRS[zone_code]
        label = f"Luzon 1911 / Philippines {zone_name}"
    return {'authid': authid, 'zone': zone_name, 'label': label, 'force_unknown': False}


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


def read_dollar_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, 'r', encoding='utf-8', errors='ignore') as handle:
        for line in handle:
            parts = [part.strip() for part in line.strip().split('$')]
            if len(parts) >= 2 and parts[0]:
                rows.append(parts)
    return rows


def load_regions():
    regions = []
    for parts in read_dollar_rows(os.path.join(LOOKUP_DIR, 'RegDta0000.Dta')):
        code = parts[0]
        short_name = parts[1] if len(parts) > 1 else code
        label = parts[2] if len(parts) > 2 else short_name
        regions.append({'code': code, 'short': short_name, 'name': label, 'display': label})
    return regions


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
            latitude = row[6].strip() if len(row) > 6 else ""
            longitude = row[7].strip() if len(row) > 7 else ""
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
                'latitude': latitude,
                'longitude': longitude,
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
        self.setWindowTitle("Tie-Line Description")
        self.resize(760, 520)
        self.regions = load_regions()
        self.provinces = load_provinces()
        self.tie_points = []

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel("GE-Survey System v2.16"))

        main_row = QtWidgets.QHBoxLayout()
        left = QtWidgets.QVBoxLayout()
        right = QtWidgets.QVBoxLayout()

        tie_group = QtWidgets.QGroupBox("TiePoint:")
        tie_form = QtWidgets.QFormLayout(tie_group)
        self.region_combo = QtWidgets.QComboBox()
        self.province_combo = QtWidgets.QComboBox()
        self.tp_id_edit = QtWidgets.QLineEdit()
        self.latitude_edit = QtWidgets.QLineEdit()
        self.longitude_edit = QtWidgets.QLineEdit()
        tie_form.addRow("Region:", self.region_combo)
        tie_form.addRow("Province:", self.province_combo)
        tie_form.addRow("TP Id:", self.tp_id_edit)
        tie_form.addRow("Latitude:", self.latitude_edit)
        tie_form.addRow("Longitude:", self.longitude_edit)
        left.addWidget(tie_group)

        projection_group = QtWidgets.QGroupBox("Projection Type")
        projection_layout = QtWidgets.QVBoxLayout(projection_group)
        self.lpcs_radio = QtWidgets.QRadioButton("LPCS")
        self.ptm_radio = QtWidgets.QRadioButton("Ptm")
        self.prs_radio = QtWidgets.QRadioButton("pRs")
        projection_layout.addWidget(self.lpcs_radio)
        projection_layout.addWidget(self.ptm_radio)
        projection_layout.addWidget(self.prs_radio)
        self.ptm_radio.setChecked(True)
        left.addWidget(projection_group)

        self.type_edit = QtWidgets.QLineEdit()
        self.li_edit = QtWidgets.QLineEdit()
        self.date_edit = QtWidgets.QLineEdit()
        misc_form = QtWidgets.QFormLayout()
        misc_form.addRow("Survey Type:", self.type_edit)
        misc_form.addRow("LI / Reference Number:", self.li_edit)
        misc_form.addRow("Date:", self.date_edit)
        left.addLayout(misc_form)
        left.addStretch()

        self.lpcs_north_edit = QtWidgets.QLineEdit()
        self.lpcs_east_edit = QtWidgets.QLineEdit()
        self.ptm_north_edit = QtWidgets.QLineEdit()
        self.ptm_east_edit = QtWidgets.QLineEdit()
        self.prs_north_edit = QtWidgets.QLineEdit()
        self.prs_east_edit = QtWidgets.QLineEdit()
        for edit in (
            self.tp_id_edit,
            self.latitude_edit,
            self.longitude_edit,
            self.lpcs_north_edit,
            self.lpcs_east_edit,
            self.ptm_north_edit,
            self.ptm_east_edit,
            self.prs_north_edit,
            self.prs_east_edit,
        ):
            edit.setReadOnly(True)
        for title, north_edit, east_edit in (
            ("LPCS:", self.lpcs_north_edit, self.lpcs_east_edit),
            ("PTM:", self.ptm_north_edit, self.ptm_east_edit),
            ("PRS:", self.prs_north_edit, self.prs_east_edit),
        ):
            coord_group = QtWidgets.QGroupBox(title)
            coord_form = QtWidgets.QFormLayout(coord_group)
            coord_form.addRow("Northing:", north_edit)
            coord_form.addRow("Easting:", east_edit)
            right.addWidget(coord_group)
        right.addStretch()

        main_row.addLayout(left)
        main_row.addLayout(right)
        layout.addLayout(main_row)

        tp_group = QtWidgets.QGroupBox("TP Descriptions:")
        tp_layout = QtWidgets.QVBoxLayout(tp_group)
        self.description_combo = QtWidgets.QComboBox()
        self.description_combo.setEditable(True)
        self.description_combo.setMinimumContentsLength(70)
        self.description_combo.setSizeAdjustPolicy(QtWidgets.QComboBox.AdjustToMinimumContentsLengthWithIcon)
        self.description_combo.setMaxVisibleItems(18)
        self.description_combo.setFont(QFont("Consolas", 9))
        self.description_combo.view().setFont(QFont("Consolas", 9))
        self.description_combo.view().setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        tp_layout.addWidget(self.description_combo)
        layout.addWidget(tp_group)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.region_combo.currentIndexChanged.connect(self.populate_provinces)
        self.province_combo.currentIndexChanged.connect(self.populate_tie_points)
        self.description_combo.currentIndexChanged.connect(self.apply_selected_tie_point)
        self.ptm_radio.toggled.connect(self.apply_projection_to_primary)
        self.prs_radio.toggled.connect(self.apply_projection_to_primary)
        self.lpcs_radio.toggled.connect(self.apply_projection_to_primary)

        self.populate_regions()

    def populate_regions(self):
        self.region_combo.blockSignals(True)
        self.region_combo.clear()
        if self.regions:
            for region in self.regions:
                self.region_combo.addItem(region.get('display', region.get('name', '')), region)
        else:
            self.region_combo.addItem("All Regions", {'code': '', 'display': 'All Regions'})
        self.region_combo.blockSignals(False)
        self.populate_provinces()

    def populate_provinces(self):
        region = self.region_combo.currentData() or {}
        prefix = str(region.get('code', ''))[:2]
        filtered = [province for province in self.provinces if not prefix or province['code'].startswith(prefix)]
        self.province_combo.blockSignals(True)
        self.province_combo.clear()
        for province in filtered:
            self.province_combo.addItem(f"{province['code']} - {province['name']}", province)
        self.province_combo.blockSignals(False)
        self.populate_tie_points()

    def populate_tie_points(self):
        province = self.province_combo.currentData() or {}
        self.tie_points = load_tie_points_for_province(province.get('code', ''))
        self.description_combo.blockSignals(True)
        self.description_combo.clear()
        for point in self.tie_points:
            self.description_combo.addItem(point.get('display', point.get('description', '')), point)
        self.description_combo.blockSignals(False)
        self.apply_selected_tie_point()

    def selected_projection(self):
        if self.prs_radio.isChecked():
            return 'prs'
        if self.lpcs_radio.isChecked():
            return 'lpcs'
        return 'ptm'

    def apply_selected_tie_point(self):
        point = self.description_combo.currentData() or {}
        self.tp_id_edit.setText(point.get('id', ''))
        self.latitude_edit.setText(point.get('latitude', ''))
        self.longitude_edit.setText(point.get('longitude', ''))
        self.type_edit.setText(point.get('survey', ''))
        self.lpcs_north_edit.setText(point.get('lpcs_n', ''))
        self.lpcs_east_edit.setText(point.get('lpcs_e', ''))
        self.ptm_north_edit.setText(point.get('ptm_n', ''))
        self.ptm_east_edit.setText(point.get('ptm_e', ''))
        self.prs_north_edit.setText(point.get('prs_n', ''))
        self.prs_east_edit.setText(point.get('prs_e', ''))
        self.apply_projection_to_primary()

    def apply_projection_to_primary(self):
        return

    def projected_values_for(self, projection):
        if projection == 'lpcs':
            return self.lpcs_north_edit.text(), self.lpcs_east_edit.text()
        if projection == 'prs':
            return self.prs_north_edit.text(), self.prs_east_edit.text()
        return self.ptm_north_edit.text(), self.ptm_east_edit.text()

    def selected_values(self):
        point = self.description_combo.currentData() or {}
        projection = self.selected_projection()
        northing, easting = self.projected_values_for(projection)
        return {
            'point': point,
            'projection': projection.upper(),
            'northing': northing,
            'easting': easting,
            'description': point.get('description', self.description_combo.currentText()),
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
        self.selected_tie_values = {}
        self.lookup_provinces = load_provinces()
        self.current_lot_id = self.generate_lot_id()
        self._loading_settings = False
        self.setup_project_detail_sections()
        self.setup_table_paste_controls()
        self.setup_sketch_preview()
        
        # Connect buttons
        self.add_corner_btn.clicked.connect(self.add_corner)
        self.remove_corner_btn.clicked.connect(self.remove_corner)
        self.plot_btn.clicked.connect(self.plot_lot)
        self.clear_btn.clicked.connect(self.clear_all)
        self.export_btn.clicked.connect(self.export_coordinates)
        try:
            self.choose_tie_btn.clicked.connect(self.open_tie_point_dialog)
        except Exception:
            pass
        self.populate_claimant_lookups()
        self.set_corner_count(4)
        self.load_saved_state()

    def setup_project_detail_sections(self):
        if hasattr(self, 'groupBox_tie_point'):
            self.groupBox_tie_point.hide()

        self.tie_details_group = QtWidgets.QGroupBox("Selected Tie Point")
        tie_form = QtWidgets.QFormLayout(self.tie_details_group)
        self.tie_name_display = QtWidgets.QLineEdit()
        self.tie_projection_display = QtWidgets.QLineEdit()
        self.tie_northing_display = QtWidgets.QLineEdit()
        self.tie_easting_display = QtWidgets.QLineEdit()
        self.tie_crs_display = QtWidgets.QLineEdit()
        for edit in (
            self.tie_name_display,
            self.tie_projection_display,
            self.tie_northing_display,
            self.tie_easting_display,
            self.tie_crs_display,
        ):
            edit.setReadOnly(True)
        tie_form.addRow("Tie Point Name:", self.tie_name_display)
        tie_form.addRow("Coordinate Source:", self.tie_projection_display)
        tie_form.addRow("Tie Point Northing:", self.tie_northing_display)
        tie_form.addRow("Tie Point Easting:", self.tie_easting_display)
        tie_form.addRow("Layer CRS:", self.tie_crs_display)

        self.claimant_group = QtWidgets.QGroupBox("Lot / Claimant Details")
        claimant_form = QtWidgets.QFormLayout(self.claimant_group)
        self.lot_id_input = QtWidgets.QLineEdit(self.current_lot_id)
        self.lot_id_input.setReadOnly(True)
        self.lot_name_input = QtWidgets.QLineEdit()
        self.ge_name_input = QtWidgets.QLineEdit()
        self.survey_number_input = QtWidgets.QLineEdit()
        self.survey_date_input = QtWidgets.QLineEdit()
        self.type_combo = QtWidgets.QComboBox()
        self.type_combo.setEditable(True)
        self.claimant_input = QtWidgets.QLineEdit()
        self.island_combo = QtWidgets.QComboBox()
        self.island_combo.setEditable(True)
        self.province_detail_combo = QtWidgets.QComboBox()
        self.province_detail_combo.setEditable(True)
        self.municipality_combo = QtWidgets.QComboBox()
        self.municipality_combo.setEditable(True)
        self.barangay_combo = QtWidgets.QComboBox()
        self.barangay_combo.setEditable(True)

        claimant_form.addRow("Lot ID:", self.lot_id_input)
        claimant_form.addRow("Lot Name / Number:", self.lot_name_input)
        claimant_form.addRow("GE / Surveyor Name:", self.ge_name_input)
        claimant_form.addRow("Survey Number:", self.survey_number_input)
        claimant_form.addRow("Survey Date:", self.survey_date_input)
        claimant_form.addRow("Type:", self.type_combo)
        claimant_form.addRow("Claimant:", self.claimant_input)
        claimant_form.addRow("Island:", self.island_combo)
        claimant_form.addRow("Province:", self.province_detail_combo)
        claimant_form.addRow("Municipality / City:", self.municipality_combo)
        claimant_form.addRow("Barangay:", self.barangay_combo)

        self.lot_details_btn = QtWidgets.QPushButton("Lot Details...")
        self.lot_details_btn.clicked.connect(self.open_lot_details_dialog)
        self.horizontalLayout.insertWidget(4, self.lot_details_btn)

        self.tie_details_group.hide()
        self.claimant_group.hide()

        self.province_detail_combo.currentIndexChanged.connect(self.on_detail_province_changed)
        self.municipality_combo.currentIndexChanged.connect(self.on_detail_municipality_changed)

    def setup_table_paste_controls(self):
        self.table.blockSignals(True)
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["Line", "Bearing", "Distance"])
        self.table.horizontalHeader().setSectionResizeMode(0, QtWidgets.QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QtWidgets.QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QtWidgets.QHeaderView.Stretch)
        self.table.setMinimumHeight(300)
        self.table.blockSignals(False)
        self.table.installEventFilter(self)
        self.table.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.table.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectItems)
        self.table.itemChanged.connect(self.on_table_item_changed)
        self.start_x_input.textChanged.connect(self.update_live_sketch)
        self.start_y_input.textChanged.connect(self.update_live_sketch)
        self.corner_count_label = QtWidgets.QLabel("Corners:")
        self.corner_count_spin = QtWidgets.QSpinBox()
        self.corner_count_spin.setMinimum(3)
        self.corner_count_spin.setMaximum(500)
        self.corner_count_spin.setValue(max(self.table.rowCount(), 4))
        self.corner_count_spin.valueChanged.connect(self.set_corner_count)
        self.paste_rows_btn = QtWidgets.QPushButton("Paste Rows")
        self.paste_rows_btn.clicked.connect(self.paste_rows_from_clipboard)
        try:
            self.horizontalLayout_2.insertWidget(0, self.corner_count_label)
            self.horizontalLayout_2.insertWidget(1, self.corner_count_spin)
            self.horizontalLayout_2.insertWidget(2, self.paste_rows_btn)
        except Exception:
            layout = self.add_corner_btn.parentWidget().layout()
            layout.insertWidget(0, self.corner_count_label)
            layout.insertWidget(1, self.corner_count_spin)
            layout.insertWidget(2, self.paste_rows_btn)

    def setup_sketch_preview(self):
        self.sketch_group = QtWidgets.QGroupBox("Live Sketch")
        sketch_layout = QtWidgets.QVBoxLayout(self.sketch_group)
        self.sketch_scene = QtWidgets.QGraphicsScene(self)
        self.sketch_view = QtWidgets.QGraphicsView(self.sketch_scene)
        self.sketch_view.setMinimumHeight(220)
        sketch_layout.addWidget(self.sketch_view)

        result_index = self.verticalLayout.indexOf(self.groupBox_3) if hasattr(self, 'groupBox_3') else -1
        self.plot_results_row = QtWidgets.QWidget()
        plot_results_layout = QtWidgets.QHBoxLayout(self.plot_results_row)
        plot_results_layout.setContentsMargins(0, 0, 0, 0)
        plot_results_layout.addWidget(self.sketch_group, 1)
        if result_index >= 0:
            self.verticalLayout.removeWidget(self.groupBox_3)
            plot_results_layout.addWidget(self.groupBox_3, 1)
            self.verticalLayout.insertWidget(result_index, self.plot_results_row)
        else:
            self.verticalLayout.insertWidget(4, self.plot_results_row)

        self.results_text.setMinimumHeight(220)
        self.update_live_sketch()

    def closeEvent(self, event):
        self.save_state()
        super().closeEvent(event)

    def reject(self):
        self.save_state()
        super().reject()

    def save_state(self):
        if getattr(self, '_loading_settings', False):
            return
        rows = []
        for row in range(self.table.rowCount()):
            bearing_item = self.table.item(row, 1)
            distance_item = self.table.item(row, 2)
            rows.append({
                'bearing': bearing_item.text() if bearing_item else '',
                'distance': distance_item.text() if distance_item else '',
            })
        state = {
            'start_x': self.start_x_input.text(),
            'start_y': self.start_y_input.text(),
            'corner_count': self.corner_count_spin.value() if hasattr(self, 'corner_count_spin') else max(len(rows) - 1, 3),
            'rows': rows,
            'lot_id': self.lot_id_input.text(),
            'lot_name': self.lot_name_input.text(),
            'ge_name': self.ge_name_input.text(),
            'survey_number': self.survey_number_input.text(),
            'survey_date': self.survey_date_input.text(),
            'type': self.type_combo.currentText(),
            'claimant': self.claimant_input.text(),
            'island': self.island_combo.currentText(),
            'province': self.province_detail_combo.currentText(),
            'municipality': self.municipality_combo.currentText(),
            'barangay': self.barangay_combo.currentText(),
            'selected_tie_values': self.selected_tie_values,
            'results': self.results_text.toPlainText(),
        }
        settings = QSettings()
        settings.setValue(SETTINGS_KEY, json.dumps(state))
        settings.sync()

    def load_saved_state(self):
        raw_state = QSettings().value(SETTINGS_KEY, '', type=str)
        if not raw_state:
            return
        try:
            state = json.loads(raw_state)
        except (TypeError, ValueError):
            return

        self._loading_settings = True
        try:
            self.start_x_input.setText(str(state.get('start_x', self.start_x_input.text())))
            self.start_y_input.setText(str(state.get('start_y', self.start_y_input.text())))

            self.current_lot_id = state.get('lot_id') or self.current_lot_id
            self.lot_id_input.setText(self.current_lot_id)
            self.lot_name_input.setText(state.get('lot_name', ''))
            self.ge_name_input.setText(state.get('ge_name', ''))
            self.survey_number_input.setText(state.get('survey_number', ''))
            self.survey_date_input.setText(state.get('survey_date', ''))
            self.type_combo.setCurrentText(state.get('type', self.type_combo.currentText()))
            self.claimant_input.setText(state.get('claimant', ''))
            self.island_combo.setCurrentText(state.get('island', self.island_combo.currentText()))

            province_text = state.get('province', '')
            municipality_text = state.get('municipality', '')
            barangay_text = state.get('barangay', '')
            if province_text:
                self.province_detail_combo.setCurrentText(province_text)
                self.on_detail_province_changed(self.province_detail_combo.currentIndex())
            if municipality_text:
                self.municipality_combo.setCurrentText(municipality_text)
                self.on_detail_municipality_changed(self.municipality_combo.currentIndex())
            if barangay_text:
                self.barangay_combo.setCurrentText(barangay_text)

            rows = state.get('rows') or []
            try:
                corner_count = int(state.get('corner_count') or max(len(rows) - 1, 3))
            except (TypeError, ValueError):
                corner_count = max(len(rows) - 1, 3)
            self.set_corner_count(max(corner_count, 3))
            self.table.blockSignals(True)
            for row_index, row_data in enumerate(rows[:self.table.rowCount()]):
                self.table.setItem(row_index, 1, QtWidgets.QTableWidgetItem(str(row_data.get('bearing', ''))))
                self.table.setItem(row_index, 2, QtWidgets.QTableWidgetItem(str(row_data.get('distance', ''))))
            self.table.blockSignals(False)

            self.selected_tie_values = state.get('selected_tie_values') or {}
            self.update_tie_detail_display()
            saved_results = state.get('results', '')
            if saved_results:
                self.results_text.setPlainText(saved_results)
        finally:
            self._loading_settings = False
            self.refresh_line_guides()
            self.update_live_sketch()

    def eventFilter(self, watched, event):
        if watched is self.table and event.type() == QEvent.KeyPress:
            if event.matches(QKeySequence.Paste):
                self.paste_rows_from_clipboard()
                return True
        return super().eventFilter(watched, event)
        
    def add_corner(self):
        """Add a new corner row to the table"""
        row = self.table.rowCount()
        self.table.insertRow(row)
        self.set_line_guide_item(row)
        self.table.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(row + 1)))
        self.sync_corner_count_spin()
        self.refresh_line_guides()
        
    def remove_corner(self):
        """Remove selected corner row"""
        if self.table.rowCount() <= self.corner_count_spin.minimum() + 1:
            return
        row = self.table.currentRow()
        if row >= 0:
            self.table.removeRow(row)
            self.refresh_corner_numbers()
            self.refresh_line_guides()
            self.sync_corner_count_spin()
            self.update_live_sketch()
    
    def clear_all(self):
        """Clear all corners"""
        self.table.setRowCount(0)
        self.results_text.clear()
        self.calculated_coordinates = []
        self.autocad_script = ""
        self.selected_tie_values = {}
        self.current_lot_id = self.generate_lot_id()
        self.lot_id_input.setText(self.current_lot_id)
        self.update_tie_detail_display()
        self.set_corner_count(4)

    def refresh_corner_numbers(self):
        for row in range(self.table.rowCount()):
            self.table.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(row + 1)))

    def set_corner_count(self, count):
        target_rows = int(count) + 1
        self.table.blockSignals(True)
        while self.table.rowCount() < target_rows:
            row = self.table.rowCount()
            self.table.insertRow(row)
            self.set_line_guide_item(row)
            self.table.setVerticalHeaderItem(row, QtWidgets.QTableWidgetItem(str(row + 1)))
        while self.table.rowCount() > target_rows:
            self.table.removeRow(self.table.rowCount() - 1)
        self.table.blockSignals(False)
        self.refresh_corner_numbers()
        self.refresh_line_guides()
        self.sync_corner_count_spin()
        self.update_live_sketch()

    def sync_corner_count_spin(self):
        if not hasattr(self, 'corner_count_spin'):
            return
        self.corner_count_spin.blockSignals(True)
        corner_count = max(self.table.rowCount() - 1, self.corner_count_spin.minimum())
        self.corner_count_spin.setValue(corner_count)
        self.corner_count_spin.blockSignals(False)

    def set_line_guide_item(self, row):
        item = QtWidgets.QTableWidgetItem("")
        item.setFlags(item.flags() & ~Qt.ItemIsEditable)
        item.setBackground(QBrush(QColor("#f0f0f0")))
        self.table.setItem(row, 0, item)

    def refresh_line_guides(self):
        count = self.table.rowCount()
        for row in range(count):
            item = self.table.item(row, 0)
            if item is None:
                self.set_line_guide_item(row)
                item = self.table.item(row, 0)
            if row == 0:
                label = "TP-1"
            elif row == count - 1:
                label = f"{row}-{1}"
            else:
                label = f"{row}-{row + 1}"
            item.setText(label)

    def on_table_item_changed(self, item):
        if item and item.column() == 0:
            return
        self.update_live_sketch()

    def paste_rows_from_clipboard(self):
        text = QtWidgets.QApplication.clipboard().text()
        rows = self.parse_pasted_bearing_distance_rows(text)
        if not rows:
            QtWidgets.QMessageBox.warning(
                self,
                "Paste Rows",
                "Clipboard does not contain bearing/distance rows. Copy two columns from the spreadsheet and try again.",
            )
            return

        start_row = self.table.currentRow()
        if start_row < 0:
            start_row = self.first_empty_table_row()
        if start_row < 0:
            start_row = self.table.rowCount()

        while self.table.rowCount() < start_row + len(rows):
            self.add_corner()

        for offset, (bearing, distance) in enumerate(rows):
            row = start_row + offset
            self.table.setItem(row, 1, QtWidgets.QTableWidgetItem(bearing))
            self.table.setItem(row, 2, QtWidgets.QTableWidgetItem(distance))
        self.refresh_corner_numbers()
        self.refresh_line_guides()
        self.sync_corner_count_spin()
        self.update_live_sketch()
        self.results_text.setText(f"Pasted {len(rows)} bearing/distance row(s).")

    def first_empty_table_row(self):
        for row in range(self.table.rowCount()):
            bearing_item = self.table.item(row, 1)
            distance_item = self.table.item(row, 2)
            bearing_blank = bearing_item is None or not bearing_item.text().strip()
            distance_blank = distance_item is None or not distance_item.text().strip()
            if bearing_blank and distance_blank:
                return row
        return -1

    def parse_pasted_bearing_distance_rows(self, text):
        rows = []
        for raw_line in str(text or "").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            cells = [cell.strip() for cell in re.split(r"\t|,", line) if cell.strip()]
            if len(cells) < 2:
                cells = [cell.strip() for cell in re.split(r"\s{2,}", line) if cell.strip()]
            if len(cells) < 2:
                cells = self.split_bearing_distance_line(line)
            if len(cells) < 2:
                continue

            bearing = cells[0]
            distance = cells[1]
            if parse_bearing(bearing) is None and len(cells) >= 3:
                bearing = cells[1]
                distance = cells[2]
            if parse_bearing(bearing) is None or parse_float(distance) is None:
                continue
            rows.append((bearing, distance))
        return rows

    def split_bearing_distance_line(self, line):
        match = re.match(r"^\s*((?:[NS]\s*)?.*?(?:\s*[EW])?)\s+([0-9][0-9,]*(?:\.\d+)?)\s*$", line, re.IGNORECASE)
        if not match:
            return []
        return [match.group(1).strip(), match.group(2).strip()]

    def preview_corners_from_table(self):
        corners = []
        for row in range(self.table.rowCount()):
            bearing_item = self.table.item(row, 1)
            distance_item = self.table.item(row, 2)
            if not bearing_item or not distance_item:
                continue
            bearing_text = bearing_item.text().strip()
            distance_text = distance_item.text().strip()
            if not bearing_text or not distance_text:
                continue
            bearing = parse_bearing(bearing_text)
            distance = parse_float(distance_text)
            if bearing is None or distance is None or distance <= 0:
                continue
            corners.append({'bearing': bearing, 'bearing_text': bearing_text, 'distance': distance})
        return corners

    def update_live_sketch(self):
        if not hasattr(self, 'sketch_scene'):
            return
        self.sketch_scene.clear()
        corners = self.preview_corners_from_table()
        if not corners:
            self.sketch_scene.addText("Enter bearings and distances to preview the lot sketch.")
            return
        coordinates = self.calculate_coordinates(0, 0, corners)
        lot_coordinates = self.display_lot_coordinates(self.lot_boundary_coordinates(coordinates))
        if len(lot_coordinates) < 2:
            self.sketch_scene.addText("Enter the lot boundary lines after TP-1 to preview the polygon.")
            return
        points = [(x, -y) for x, y in lot_coordinates]
        xs = [point[0] for point in points]
        ys = [point[1] for point in points]
        min_x, max_x = min(xs), max(xs)
        min_y, max_y = min(ys), max(ys)
        width = max(max_x - min_x, 1)
        height = max(max_y - min_y, 1)
        margin = max(width, height) * 0.15

        line_pen = QPen(QColor("#1f77b4"), 2)
        close_pen = QPen(QColor("#888888"), 1, Qt.DashLine)
        point_brush = QBrush(QColor("#1f77b4"))
        for index in range(len(points) - 1):
            x1, y1 = points[index]
            x2, y2 = points[index + 1]
            self.sketch_scene.addLine(x1, y1, x2, y2, line_pen)
            self.sketch_scene.addEllipse(x1 - 1.5, y1 - 1.5, 3, 3, line_pen, point_brush)
            self.sketch_scene.addText(str(index + 1)).setPos(x1 + 2, y1 + 2)
        if len(points) > 2:
            self.sketch_scene.addLine(points[-1][0], points[-1][1], points[0][0], points[0][1], close_pen)
        self.sketch_scene.addEllipse(points[-1][0] - 1.5, points[-1][1] - 1.5, 3, 3, line_pen, point_brush)

        self.sketch_scene.setSceneRect(min_x - margin, min_y - margin, width + 2 * margin, height + 2 * margin)
        self.sketch_view.fitInView(self.sketch_scene.sceneRect(), Qt.KeepAspectRatio)

    def generate_lot_id(self):
        existing = [
            layer for layer in QgsProject.instance().mapLayers().values()
            if layer.name().startswith("Lot Boundary")
        ]
        return f"LOT-{len(existing) + 1:03d}"

    def populate_claimant_lookups(self):
        self.type_combo.clear()
        self.type_combo.addItems(load_simple_lookup_values('SurveyTypes.csv', SURVEY_TYPES))
        self.island_combo.clear()
        self.island_combo.addItems(load_simple_lookup_values('IslandGroups.csv', ISLAND_GROUPS))
        self.province_detail_combo.blockSignals(True)
        self.province_detail_combo.clear()
        for province in self.lookup_provinces:
            self.province_detail_combo.addItem(province['name'], province)
        self.province_detail_combo.blockSignals(False)
        self.on_detail_province_changed(self.province_detail_combo.currentIndex())

    def on_detail_province_changed(self, index):
        province = self.province_detail_combo.itemData(index) or {}
        province_code = province.get('code', '')
        island = PROVINCE_ISLANDS.get(normalize_lookup_name(province.get('name', '')))
        if island:
            self.select_combo_text(self.island_combo, island)
        municipalities = load_municipalities_for_province(province_code)
        self.municipality_combo.blockSignals(True)
        self.municipality_combo.clear()
        for municipality in municipalities:
            self.municipality_combo.addItem(municipality['name'], municipality)
        self.municipality_combo.blockSignals(False)
        self.on_detail_municipality_changed(self.municipality_combo.currentIndex())

    def on_detail_municipality_changed(self, index):
        municipality = self.municipality_combo.itemData(index) or {}
        barangays = load_barangays_for_municipality(municipality.get('code', ''))
        self.barangay_combo.blockSignals(True)
        self.barangay_combo.clear()
        for barangay in barangays:
            self.barangay_combo.addItem(barangay['name'], barangay)
        self.barangay_combo.blockSignals(False)

    def select_combo_text(self, combo, text):
        for index in range(combo.count()):
            if combo.itemText(index).upper() == str(text).upper():
                combo.setCurrentIndex(index)
                return True
        return False

    def select_combo_data_name(self, combo, name):
        normalized = normalize_lookup_name(name)
        for index in range(combo.count()):
            data = combo.itemData(index) or {}
            if normalize_lookup_name(data.get('name', combo.itemText(index))) == normalized:
                combo.setCurrentIndex(index)
                return True
        return False

    def select_tie_point_coordinates(self, point):
        for projection, x_key, y_key in [('PTM', 'ptm_e', 'ptm_n'), ('PRS', 'prs_e', 'prs_n'), ('LPCS', 'lpcs_e', 'lpcs_n')]:
            x = parse_float(point.get(x_key))
            y = parse_float(point.get(y_key))
            if x is not None and y is not None:
                return x, y, projection
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
            self.selected_tie_values = values
            self.apply_tie_point_to_details()
            self.update_tie_detail_display()
            self.results_text.setText(
                f"Selected tie point: {values.get('description', '')}\n"
                f"Coordinate source: {values.get('projection', '')}\n"
                f"Coordinates set to: ({x:.3f}, {y:.3f})"
            )

    def apply_tie_point_to_details(self):
        point = self.selected_tie_values.get('point') or {}
        if point.get('province') and self.select_combo_data_name(self.province_detail_combo, point.get('province')):
            pass
        if point.get('municipality'):
            self.select_combo_data_name(self.municipality_combo, point.get('municipality'))

    def update_tie_detail_display(self):
        values = self.selected_tie_values or {}
        point = values.get('point') or {}
        crs_info = crs_for_tie_point(values)
        crs_label = crs_info.get('label', '')
        if crs_info.get('authid'):
            crs_label = f"{crs_label} ({crs_info.get('authid')})"
        elif crs_info.get('force_unknown'):
            crs_label = "Unknown CRS (LPCS)"
        self.tie_name_display.setText(values.get('description', ''))
        self.tie_projection_display.setText(values.get('projection', ''))
        self.tie_northing_display.setText(str(values.get('northing', '')))
        self.tie_easting_display.setText(str(values.get('easting', '')))
        self.tie_crs_display.setText(crs_label)

    def lot_metadata(self, area):
        point = self.selected_tie_values.get('point') or {}
        return {
            'lot_id': self.lot_id_input.text().strip() or self.current_lot_id,
            'lot_name': self.lot_name_input.text().strip(),
            'ge_name': self.ge_name_input.text().strip(),
            'survey_no': self.survey_number_input.text().strip(),
            'survey_dt': self.survey_date_input.text().strip(),
            'type': self.type_combo.currentText().strip(),
            'claimant': self.claimant_input.text().strip(),
            'island': self.island_combo.currentText().strip(),
            'province': self.province_detail_combo.currentText().strip(),
            'mun_city': self.municipality_combo.currentText().strip(),
            'barangay': self.barangay_combo.currentText().strip(),
            'area_sqm': area,
            'tie_north': parse_float(self.selected_tie_values.get('northing')),
            'tie_east': parse_float(self.selected_tie_values.get('easting')),
            'tie_name': self.selected_tie_values.get('description', point.get('description', '')),
        }

    def open_lot_details_dialog(self):
        dialog = QtWidgets.QDialog(self)
        dialog.setWindowTitle("Lot / Claimant Details")
        dialog.resize(520, 520)
        layout = QtWidgets.QVBoxLayout(dialog)
        form = QtWidgets.QFormLayout()
        layout.addLayout(form)

        lot_id = QtWidgets.QLineEdit(self.lot_id_input.text())
        lot_id.setReadOnly(True)
        lot_name = QtWidgets.QLineEdit(self.lot_name_input.text())
        ge_name = QtWidgets.QLineEdit(self.ge_name_input.text())
        survey_number = QtWidgets.QLineEdit(self.survey_number_input.text())
        survey_date = QtWidgets.QLineEdit(self.survey_date_input.text())
        type_combo = self.clone_combo(self.type_combo)
        claimant = QtWidgets.QLineEdit(self.claimant_input.text())
        island_combo = self.clone_combo(self.island_combo)
        province_combo = QtWidgets.QComboBox()
        province_combo.setEditable(True)
        for province in self.lookup_provinces:
            province_combo.addItem(province['name'], province)
        province_combo.setCurrentText(self.province_detail_combo.currentText())
        municipality_combo = QtWidgets.QComboBox()
        municipality_combo.setEditable(True)
        barangay_combo = QtWidgets.QComboBox()
        barangay_combo.setEditable(True)

        def populate_municipalities():
            province = province_combo.currentData() or {}
            island = PROVINCE_ISLANDS.get(normalize_lookup_name(province.get('name', province_combo.currentText())))
            if island:
                island_combo.setCurrentText(island)
            current = municipality_combo.currentText()
            municipality_combo.blockSignals(True)
            municipality_combo.clear()
            for municipality in load_municipalities_for_province(province.get('code', '')):
                municipality_combo.addItem(municipality['name'], municipality)
            municipality_combo.setCurrentText(current or self.municipality_combo.currentText())
            municipality_combo.blockSignals(False)
            populate_barangays()

        def populate_barangays():
            municipality = municipality_combo.currentData() or {}
            current = barangay_combo.currentText()
            barangay_combo.clear()
            for barangay in load_barangays_for_municipality(municipality.get('code', '')):
                barangay_combo.addItem(barangay['name'], barangay)
            barangay_combo.setCurrentText(current or self.barangay_combo.currentText())

        province_combo.currentIndexChanged.connect(populate_municipalities)
        municipality_combo.currentIndexChanged.connect(populate_barangays)
        populate_municipalities()

        form.addRow("Lot ID:", lot_id)
        form.addRow("Lot Name / Number:", lot_name)
        form.addRow("GE / Surveyor Name:", ge_name)
        form.addRow("Survey Number:", survey_number)
        form.addRow("Survey Date:", survey_date)
        form.addRow("Type:", type_combo)
        form.addRow("Claimant:", claimant)
        form.addRow("Island:", island_combo)
        form.addRow("Province:", province_combo)
        form.addRow("Municipality / City:", municipality_combo)
        form.addRow("Barangay:", barangay_combo)

        buttons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel)
        buttons.accepted.connect(dialog.accept)
        buttons.rejected.connect(dialog.reject)
        layout.addWidget(buttons)
        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            self.lot_name_input.setText(lot_name.text())
            self.ge_name_input.setText(ge_name.text())
            self.survey_number_input.setText(survey_number.text())
            self.survey_date_input.setText(survey_date.text())
            self.type_combo.setCurrentText(type_combo.currentText())
            self.claimant_input.setText(claimant.text())
            self.island_combo.setCurrentText(island_combo.currentText())
            self.province_detail_combo.setCurrentText(province_combo.currentText())
            self.municipality_combo.setCurrentText(municipality_combo.currentText())
            self.barangay_combo.setCurrentText(barangay_combo.currentText())

    def clone_combo(self, source):
        combo = QtWidgets.QComboBox()
        combo.setEditable(source.isEditable())
        for index in range(source.count()):
            combo.addItem(source.itemText(index))
        combo.setCurrentText(source.currentText())
        return combo
        
    def get_corners_from_table(self):
        """Extract bearing/distance data from table"""
        corners = []
        for row in range(self.table.rowCount()):
            try:
                bearing_item = self.table.item(row, 1)
                distance_item = self.table.item(row, 2)

                bearing_text = bearing_item.text().strip() if bearing_item else ""
                distance_text = distance_item.text().strip() if distance_item else ""
                if not bearing_text or not distance_text:
                    QtWidgets.QMessageBox.warning(self, "Input Error", f"Row {row + 1}: Missing bearing or distance.")
                    return None
                distance = parse_float(distance_text)
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
            
            if not corners or len(corners) < 4:
                QtWidgets.QMessageBox.warning(self, "Input Error", 
                    "Please enter the tie line and at least 3 lot boundary lines.")
                return
                
            # Calculate coordinates
            coordinates = self.calculate_coordinates(start_x, start_y, corners)
            lot_coordinates = self.lot_boundary_coordinates(coordinates)
            self.calculated_coordinates = lot_coordinates  # Store for export
            self.autocad_script = self.generate_autocad_script(lot_coordinates)
            area = self.calculate_area(lot_coordinates)
            closure_error = self.calculate_closure_error(lot_coordinates)
            metadata = self.lot_metadata(area)
            
            # Display results with coordinates
            results = f"=== LOT PLOTTER RESULTS ===\n\n"
            results += f"Lot ID: {metadata['lot_id']}\n"
            if metadata['lot_name']:
                results += f"Lot Name / Number: {metadata['lot_name']}\n"
            if metadata['claimant']:
                results += f"Claimant: {metadata['claimant']}\n"
            results += f"Starting Point: ({start_x:.2f}, {start_y:.2f})\n\n"
            crs_info = crs_for_tie_point(self.selected_tie_values)
            crs_authid = crs_info.get('authid')
            crs_zone = crs_info.get('zone', '')
            if crs_authid:
                results += f"Layer CRS: {crs_info.get('label')} ({crs_authid})\n\n"
            elif crs_info.get('force_unknown'):
                results += "Layer CRS: Unknown / local floating coordinates (LPCS)\n\n"
            results += f"Traverse Lines:\n"
            for i, corner in enumerate(corners, start=1):
                results += (
                    f"  Line {i}: {corner['bearing_text']} "
                    f"(azimuth {corner['bearing']:.6f})  {corner['distance']:.3f}\n"
                )
            results += "\n"
            results += f"Lot Corner Coordinates:\n"
            display_coordinates = self.display_lot_coordinates(lot_coordinates)
            for i, (x, y) in enumerate(display_coordinates, start=1):
                results += f"  Corner {i}: ({x:.2f}, {y:.2f})\n"
            results += f"\n=== CALCULATIONS ===\n"
            results += f"Area: {area:.2f} sq units\n"
            results += f"Closure Error: {closure_error:.4f} units\n"
            results += f"Number of corners: {len(display_coordinates)}\n"
            
            # Closure ratio (acceptable usually < 1:1000)
            perimeter = self.calculate_perimeter(lot_coordinates)
            if perimeter > 0 and closure_error > 0:
                results += f"Closure Ratio: 1:{perimeter/closure_error:.0f}\n"
            elif perimeter > 0:
                results += "Closure Ratio: Perfect closure\n"
            results += f"Perimeter: {perimeter:.2f} units\n"
            results += "\n=== AUTOCAD PLINE SCRIPT ===\n"
            results += self.autocad_script
            
            self.results_text.setText(results)
            
            # Create and add layer to map
            self.create_lot_layer(lot_coordinates, metadata, crs_authid, crs_zone, crs_info.get('force_unknown', False))
            
            QtWidgets.QMessageBox.information(self, "Success", 
                f"Lot plotted successfully!\nArea: {area:.2f} sq units\nClosure Error: {closure_error:.4f}")
            self.current_lot_id = self.generate_lot_id()
            self.lot_id_input.setText(self.current_lot_id)
                
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

    def lot_boundary_coordinates(self, traverse_coordinates):
        return list(traverse_coordinates[1:])

    def display_lot_coordinates(self, lot_coordinates):
        coordinates = list(lot_coordinates)
        if len(coordinates) > 1:
            first = coordinates[0]
            last = coordinates[-1]
            if math.hypot(last[0] - first[0], last[1] - first[1]) < 1e-7:
                coordinates.pop()
        return coordinates
    
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
    
    def create_lot_layer(self, coordinates, metadata, crs_authid=None, crs_zone="", force_unknown_crs=False):
        """Create a vector layer and add the lot polygon"""
        if not self.iface:
            return
        
        if force_unknown_crs:
            crs_authid = ""
            layer_uri = "Polygon"
        elif crs_authid:
            layer_uri = f"Polygon?crs={crs_authid}"
        else:
            project_crs = QgsProject.instance().crs()
            crs_authid = project_crs.authid() if project_crs and project_crs.isValid() else "EPSG:4326"
            layer_uri = f"Polygon?crs={crs_authid}"
        layer = QgsVectorLayer(layer_uri, "Lot Boundary", "memory")
        provider = layer.dataProvider()
        provider.addAttributes([
            QgsField("lot_id", QVariant.String),
            QgsField("lot_name", QVariant.String),
            QgsField("ge_name", QVariant.String),
            QgsField("survey_no", QVariant.String),
            QgsField("survey_dt", QVariant.String),
            QgsField("type", QVariant.String),
            QgsField("claimant", QVariant.String),
            QgsField("island", QVariant.String),
            QgsField("province", QVariant.String),
            QgsField("mun_city", QVariant.String),
            QgsField("barangay", QVariant.String),
            QgsField("area", QVariant.Double),
            QgsField("area_sqm", QVariant.Double),
            QgsField("perimeter", QVariant.Double),
            QgsField("closure", QVariant.Double),
            QgsField("corners", QVariant.Int),
            QgsField("tie_north", QVariant.Double),
            QgsField("tie_east", QVariant.Double),
            QgsField("tie_name", QVariant.String),
            QgsField("crs_authid", QVariant.String),
            QgsField("crs_zone", QVariant.String),
        ])
        layer.updateFields()
        
        # Create feature with polygon geometry
        points = [QgsPointXY(x, y) for x, y in self.display_lot_coordinates(coordinates)]
        points.append(QgsPointXY(points[0].x(), points[0].y()))  # Close polygon
        
        feature = QgsFeature()
        geometry = QgsGeometry.fromPolygonXY([points])
        feature.setGeometry(geometry)
        feature.setAttributes([
            metadata.get('lot_id', self.current_lot_id),
            metadata.get('lot_name', ''),
            metadata.get('ge_name', ''),
            metadata.get('survey_no', ''),
            metadata.get('survey_dt', ''),
            metadata.get('type', ''),
            metadata.get('claimant', ''),
            metadata.get('island', ''),
            metadata.get('province', ''),
            metadata.get('mun_city', ''),
            metadata.get('barangay', ''),
            geometry.area(),
            metadata.get('area_sqm', geometry.area()),
            geometry.length(),
            self.calculate_closure_error(coordinates),
            max(len(coordinates) - 1, 0),
            metadata.get('tie_north'),
            metadata.get('tie_east'),
            metadata.get('tie_name', ''),
            crs_authid,
            crs_zone,
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
        if self.dialog:
            self.dialog.save_state()
        self.iface.removePluginMenu('&Lot Plotter', self.action)
        self.iface.removeToolBarIcon(self.action)
    
    def run(self):
        """Execute the plugin"""
        if not self.dialog:
            self.dialog = LotPlotterDialog(self.iface.mainWindow())
            self.dialog.iface = self.iface
        
        self.dialog.show()
