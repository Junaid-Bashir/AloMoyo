#!/usr/bin/env python3
# scripts/load_afpostal.py

import os
import sys
from sqlmodel import SQLModel, create_engine, Session
from app.core.config       import settings
from app.models.postal_code import PostalCode

# ─── 0) Ensure we’re in project root ───────────────────────────────────────
SCRIPT_DIR   = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.abspath(os.path.join(SCRIPT_DIR, os.pardir))
if not os.path.isdir(os.path.join(PROJECT_ROOT, "app")):
    print("❌ Please run from project root (so that ./app exists)", file=sys.stderr)
    sys.exit(1)

# ─── 1) Add root to path ───────────────────────────────────────────────────
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ─── 2) Locate data file ──────────────────────────────────────────────────
DATA_FILE = os.path.join(PROJECT_ROOT, "africa_postalcodes.txt")
if not os.path.isfile(DATA_FILE):
    print(f"❌ Could not find data file: {DATA_FILE}", file=sys.stderr)
    sys.exit(1)

def parse_row(line: str):
    """Split a line into fields, trying tab, then comma, then whitespace."""
    line = line.rstrip("\n")
    if "\t" in line:
        parts = line.split("\t")
    elif "," in line:
        parts = line.split(",")
    else:
        parts = line.split()
    return [p.strip() for p in parts if p.strip()]

def main():
    engine = create_engine(settings.database_url, echo=True)
    SQLModel.metadata.create_all(engine)
    print("▶ All tables created (including postalcode)", file=sys.stderr)

    loaded = skipped = 0
    with open(DATA_FILE, encoding="utf-8") as f:
        for raw in f:
            # skip empty or comment lines
            if not raw.strip() or raw.startswith("#"):
                continue

            row = parse_row(raw)
            # Expect at least 7 fields: [cc, postal, place, admin1, admin1code, lat, lon, ...]
            if len(row) < 7:
                skipped += 1
                continue

            country    = row[0]
            code       = row[1]
            place_name = row[2]

            # the 6th & 7th fields are latitude and longitude
            lat_str = row[5]
            lon_str = row[6]

            if not lat_str or not lon_str:
                skipped += 1
                continue

            try:
                latitude  = float(lat_str)
                longitude = float(lon_str)
            except ValueError:
                skipped += 1
                continue

            with Session(engine) as session:
                session.add(
                    PostalCode(
                        country_code=country,
                        postal_code=code,
                        place_name=place_name,
                        latitude=latitude,
                        longitude=longitude,
                    )
                )
                session.commit()
            loaded += 1

    print(f"✅ Loaded {loaded} postal codes, skipped {skipped} invalid rows", file=sys.stderr)


if __name__ == "__main__":
    main()
