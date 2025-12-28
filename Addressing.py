import sqlite3
import math
import folium
import requests
from shapely.geometry import box
import webbrowser
import os

DB_file = "location.db"
location_name = input("Enter your desired location:\n").strip()
radius_km = 1

MAP_FILE = f"locations\\{location_name}.html"

conn = sqlite3.connect(DB_file)
crsr = conn.cursor()

def get_location(name):
    crsr.execute(
        "SELECT latitude, longitude FROM coordinates WHERE name=?",
        (name,)
    )
    row = crsr.fetchone()

    if row:
        print("Location found in database. Using cached data.")
        return float(row[0]), float(row[1]), True

    try:
        print("Fetching location from API...")
        params = {"q": name, "format": "json"}
        headers = {"User-Agent": "my-osm-app/1.0"}
        url = "https://nominatim.openstreetmap.org/search"

        response = requests.get(url, params=params, headers=headers, timeout=10)
        data = response.json()

        if not data:
            print(" No results found from API.")
            return None, None, False

        lat = float(data[0]["lat"])
        lon = float(data[0]["lon"])

        crsr.execute(
            "INSERT INTO coordinates(name, latitude, longitude) VALUES(?, ?, ?)",
            (name, lat, lon)
        )
        conn.commit()

        print("Location fetched and saved to database.")
        return lat, lon, False

    except Exception:
        print("Cannot fetch location (offline or API error).")
        return None, None, False

lat, lon, is_cached = get_location(location_name)

if lat is None or lon is None:
    print("Cannot display map: location unknown.")
    exit()

if is_cached and os.path.exists(MAP_FILE):
    print("Map already exists. Opening cached map.")
    webbrowser.open(MAP_FILE)
    exit()

lat_delta = radius_km / 111
lon_delta = radius_km / (111 * math.cos(math.radians(lat)))

min_lat = lat - lat_delta
max_lat = lat + lat_delta
min_lon = lon - lon_delta
max_lon = lon + lon_delta
bbox_polygon = box(min_lon, min_lat, max_lon, max_lat)

m = folium.Map(location=[lat, lon], zoom_start=17)

folium.Marker(
    [lat, lon],
    popup=location_name,
    icon=folium.Icon(color="red", icon="circle", prefix="fa")
).add_to(m)

m.save(MAP_FILE)
print("Map created and saved.")

webbrowser.open(MAP_FILE)
