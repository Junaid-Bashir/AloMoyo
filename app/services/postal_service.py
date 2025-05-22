# File: app/services/postal_service.py

from typing import Optional, List
from scipy.spatial import KDTree
from sqlmodel import Session, select
from app.database.db import engine
from app.models.postal_code import PostalCode
from app.data.ug_district_iso import lookup_iso

class PostalCodeEntry:
    """
    A container for postal code lookup results.
    """
    def __init__(self, postal_code: str, place_name: str, latitude: float, longitude: float):
        self.postal_code = postal_code
        self.place_name = place_name
        self.latitude = latitude
        self.longitude = longitude

class PostalService:
    """
    Provides nearest-neighbor postal code lookups via a KDTree.
    For Uganda (country_code='ug'), it replaces the generic postal_code
    with the ISO 3166-2:UG code for that district name.
    """
    def __init__(self):
        # Load all PostalCode rows into memory
        with Session(engine) as session:
            records = session.exec(select(PostalCode)).all()

        # Build entries list
        self.entries: List[PostalCodeEntry] = [
            PostalCodeEntry(r.postal_code, r.place_name, r.latitude, r.longitude)
            for r in records
        ]
        # Prepare coordinate list for KDTree
        coords = [(e.latitude, e.longitude) for e in self.entries]

        # Only build KDTree if data exists
        if coords:
            self.tree = KDTree(coords)
        else:
            self.tree = None

    def nearest(self, lat: float, lon: float, country_code: Optional[str] = None) -> PostalCodeEntry:
        """
        Find the nearest PostalCodeEntry to (lat, lon).
        If country_code == 'ug', override the returned postal_code with
        the ISO 3166-2:UG code for that district name.
        """
        if not self.tree:
            # No postal data loaded; return default entry
            return PostalCodeEntry("", "", lat, lon)

        # Query KDTree
        _, idx = self.tree.query((lat, lon))
        entry = self.entries[idx]

        # Override for Uganda
        if country_code and country_code.lower() == "ug":
            iso = lookup_iso(entry.place_name)
            if iso:
                entry.postal_code = iso

        return entry

# Singleton factory
_postal_service: Optional[PostalService] = None

def get_postal_service() -> PostalService:
    """
    Dependency-injectable factory for a singleton PostalService.
    """
    global _postal_service
    if _postal_service is None:
        _postal_service = PostalService()
    return _postal_service
