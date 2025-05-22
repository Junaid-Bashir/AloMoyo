# app/services/__init__.py

"""
app.services package

Provides core service utilities for AloKazi:
- get_road_name: reverse-geocoding street names
- get_postal_service / PostalService: KDTree postal lookups
"""

from .geocode import get_road_name
from .postal_service import get_postal_service, PostalService
