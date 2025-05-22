#!/usr/bin/env python3
import sys, os, sqlite3
from itertools import islice

# ── Bootstrap so __file__ relative paths work ──
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

DB_PATH   = os.path.join(project_root, "alokazi.db")
TXT_PATH  = os.path.join(project_root, "africa_postalcodes.txt")

# Debug: environment & paths
print("=== DEBUG INFO ===", file=sys.stderr)
print("Working dir:   ", os.getcwd(), file=sys.stderr)
print("Project root:  ", project_root, file=sys.stderr)
print("DB path:       ", DB_PATH, file=sys.stderr)
print("DB exists:     ", os.path.exists(DB_PATH), file=sys.stderr)
print("TXT path:      ", TXT_PATH, file=sys.stderr)
print("TXT exists:    ", os.path.exists(TXT_PATH), file=sys.stderr)
if os.path.exists(TXT_PATH):
    size = os.path.getsize(TXT_PATH)
    print(f"TXT size:      {size:,} bytes", file=sys.stderr)
    # peek at first 5 lines
    with open(TXT_PATH, encoding="utf-8") as f:
        print("First 5 lines of TXT:", file=sys.stderr)
        for L in islice(f, 5):
            print("  ", repr(L.rstrip("\n")), file=sys.stderr)
        print("...", file=sys.stderr)

# 1) Connect & ensure table exists
conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()
cur.execute("PRAGMA foreign_keys=ON;")
cur.execute("""
CREATE TABLE IF NOT EXISTS postalcode (
    id INTEGER PRIMARY KEY,
    country_code TEXT NOT NULL,
    admin_name1 TEXT,
    admin_name2 TEXT,
    place_name TEXT NOT NULL,
    postal_code TEXT NOT NULL,
    latitude REAL NOT NULL,
    longitude REAL NOT NULL
);
""")
conn.commit()

# 2) Gather rows
to_insert = []
if os.path.exists(TXT_PATH):
    with open(TXT_PATH, encoding="utf-8") as f:
        for idx, line in enumerate(f, 1):
            cols = line.rstrip("\n").split("\t")
            if len(cols) < 7:
                print(f"Skipping line {idx}: only {len(cols)} columns", file=sys.stderr)
                continue
            cc = cols[0]
            postal = cols[1]; place = cols[2]
            lat_s, lon_s = cols[5], cols[6]
            try:
                lat = float(lat_s); lon = float(lon_s)
            except ValueError:
                print(f"Skipping line {idx}: invalid coords {lat_s}, {lon_s}", file=sys.stderr)
                continue
            to_insert.append((cc, "", "", place, postal, lat, lon))

# Debug: what we gathered
print(f"Prepared {len(to_insert)} rows for insertion", file=sys.stderr)
if to_insert:
    print("Sample row:", to_insert[0], file=sys.stderr)

# 3) Insert
cur.executemany("""
INSERT INTO postalcode
  (country_code, admin_name1, admin_name2, place_name, postal_code, latitude, longitude)
VALUES (?, ?, ?, ?, ?, ?, ?)
""", to_insert)
conn.commit()

# 4) Verify
cur.execute("SELECT COUNT(*) FROM postalcode;")
count = cur.fetchone()[0]
print(f"After insert, postalcode table has {count} rows", file=sys.stderr)

# Dump first 3 rows to verify
cur.execute("SELECT * FROM postalcode LIMIT 3;")
for row in cur.fetchall():
    print("Sample DB row:", row, file=sys.stderr)

conn.close()
print("=== DEBUG RUN COMPLETE ===", file=sys.stderr)
