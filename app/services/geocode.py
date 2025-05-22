# app/services/geocode.py

from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut
import ssl
import certifi

# Create a global geolocator with SSL context for OSM
ssl_ctx = ssl.create_default_context(cafile=certifi.where())
geolocator = Nominatim(user_agent="alokazi_app", ssl_context=ssl_ctx)

def get_road_name(lat: float, lon: float) -> str:
    """
    Given latitude and longitude, reverse-geocode via OpenStreetMap
    and return the road/street name if available.
    """
    try:
        location = geolocator.reverse((lat, lon), exactly_one=True, timeout=10)
        address = location.raw.get("address", {})
        # Try common address keys for roads
        return (
            address.get("road")
            or address.get("pedestrian")
            or address.get("footway")
            or address.get("path")
            or "Unknown road"
        )
    except GeocoderTimedOut:
        return "Geocoder timeout"
    except Exception:
        return "Unknown road"
