import csv
import os
import re
import sqlite3


ROOT_DIR = os.path.dirname(os.path.dirname(__file__))
LOOKUP_DIR = os.path.join(ROOT_DIR, "LookUpData")
OUTPUT_DB = os.path.join(LOOKUP_DIR, "lookup.sqlite")


def parse_float_or_blank(value):
    try:
        text = str(value).strip()
        if text == "":
            return ""
        return f"{float(text):.3f}".rstrip("0").rstrip(".")
    except (TypeError, ValueError):
        return ""


def read_dollar_rows(path):
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            parts = [part.strip() for part in line.strip().split("$")]
            if len(parts) >= 2 and parts[0] and parts[1]:
                rows.append(parts)
    return rows


def read_prefixed_dollar_rows(prefix):
    rows = []
    for extension in ("Txt", "Dta", "csv"):
        for name in sorted(os.listdir(LOOKUP_DIR)):
            if not name.lower().startswith(prefix.lower()) or not name.lower().endswith(f".{extension.lower()}"):
                continue
            rows.extend(read_dollar_rows(os.path.join(LOOKUP_DIR, name)))

    seen = set()
    unique = []
    for parts in rows:
        code = parts[0]
        if code in seen:
            continue
        seen.add(code)
        unique.append((code, parts[1]))
    return unique


def load_regions():
    rows = []
    for parts in read_dollar_rows(os.path.join(LOOKUP_DIR, "RegDta0000.Dta")):
        code = parts[0]
        short_name = parts[1] if len(parts) > 1 else code
        label = parts[2] if len(parts) > 2 else short_name
        rows.append((code, short_name, label, label))
    return rows


def load_provinces():
    rows = []
    with open(os.path.join(LOOKUP_DIR, "PrvDta.csv"), "r", encoding="utf-8", errors="ignore", newline="") as handle:
        for row in csv.reader(handle):
            if len(row) >= 2 and row[0].strip():
                rows.append((row[0].strip(), row[1].strip()))
    return rows


def load_simple_values(file_name, category):
    path = os.path.join(LOOKUP_DIR, file_name)
    rows = []
    if not os.path.exists(path):
        return rows
    with open(path, "r", encoding="utf-8", errors="ignore", newline="") as handle:
        for index, row in enumerate(csv.reader(handle)):
            if row and row[0].strip():
                rows.append((category, row[0].strip(), index))
    return rows


def load_tie_points(provinces):
    rows = []
    province_codes = {code for code, _name in provinces}
    for name in sorted(os.listdir(LOOKUP_DIR)):
        stem, extension = os.path.splitext(name)
        if extension.lower() != ".csv" or not re.fullmatch(r"\d{4}", stem) or stem not in province_codes:
            continue
        path = os.path.join(LOOKUP_DIR, name)
        with open(path, "r", encoding="utf-8-sig", errors="ignore", newline="") as handle:
            for row_order, row in enumerate(csv.reader(handle)):
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
                rows.append((
                    stem, row_order, number, description, display, point_name, marker, survey,
                    municipality, province, region, latitude, longitude, lpcs_n, lpcs_e,
                    prs_n, prs_e, ptm_n, ptm_e,
                ))
    return rows


def create_schema(connection):
    connection.executescript(
        """
        DROP TABLE IF EXISTS regions;
        DROP TABLE IF EXISTS provinces;
        DROP TABLE IF EXISTS municipalities;
        DROP TABLE IF EXISTS barangays;
        DROP TABLE IF EXISTS simple_values;
        DROP TABLE IF EXISTS tie_points;

        CREATE TABLE regions (
            code TEXT PRIMARY KEY,
            short TEXT,
            name TEXT,
            display TEXT
        );

        CREATE TABLE provinces (
            code TEXT PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE municipalities (
            code TEXT PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE barangays (
            code TEXT PRIMARY KEY,
            name TEXT
        );

        CREATE TABLE simple_values (
            category TEXT,
            value TEXT,
            sort_order INTEGER,
            PRIMARY KEY (category, value)
        );

        CREATE TABLE tie_points (
            province_code TEXT,
            row_order INTEGER,
            id TEXT,
            description TEXT,
            display TEXT,
            point_name TEXT,
            marker TEXT,
            survey TEXT,
            municipality TEXT,
            province TEXT,
            region TEXT,
            latitude TEXT,
            longitude TEXT,
            lpcs_n TEXT,
            lpcs_e TEXT,
            prs_n TEXT,
            prs_e TEXT,
            ptm_n TEXT,
            ptm_e TEXT,
            PRIMARY KEY (province_code, row_order)
        );

        CREATE INDEX idx_tie_points_province ON tie_points (province_code, row_order);
        CREATE INDEX idx_municipalities_code ON municipalities (code);
        CREATE INDEX idx_barangays_code ON barangays (code);
        """
    )


def main():
    provinces = load_provinces()
    if os.path.exists(OUTPUT_DB):
        os.remove(OUTPUT_DB)
    with sqlite3.connect(OUTPUT_DB) as connection:
        create_schema(connection)
        connection.executemany("INSERT INTO regions VALUES (?, ?, ?, ?)", load_regions())
        connection.executemany("INSERT INTO provinces VALUES (?, ?)", provinces)
        connection.executemany("INSERT INTO municipalities VALUES (?, ?)", read_prefixed_dollar_rows("MunDta"))
        connection.executemany("INSERT INTO barangays VALUES (?, ?)", read_prefixed_dollar_rows("BgyDta"))
        simple_values = []
        simple_values.extend(load_simple_values("SurveyTypes.csv", "SurveyTypes"))
        simple_values.extend(load_simple_values("IslandGroups.csv", "IslandGroups"))
        connection.executemany("INSERT INTO simple_values VALUES (?, ?, ?)", simple_values)
        connection.executemany(
            """
            INSERT INTO tie_points (
                province_code, row_order, id, description, display, point_name, marker,
                survey, municipality, province, region, latitude, longitude, lpcs_n,
                lpcs_e, prs_n, prs_e, ptm_n, ptm_e
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            load_tie_points(provinces),
        )
        connection.commit()
        connection.execute("VACUUM")

    print(f"Compiled lookup database: {OUTPUT_DB}")


if __name__ == "__main__":
    main()
