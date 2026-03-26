import json
import csv

# GeoJSON-Datei einlesen
with open('gemeinden_simplify200.geojson', 'r', encoding='utf-8') as f:
    data = json.load(f)

gemeinden_liste = []

for feature in data['features']:
    props = feature['properties']
    
    # Filter: Nur Nordrhein-Westfalen (SN_L == '05')
    if props.get('SN_L') == '05':
        name = props.get('GEN')
        destatis = props.get('destatis', {})
        
        # Koordinaten auslesen und Komma durch Punkt ersetzen für valides Float-Format
        lat_str = destatis.get('center_lat', '0').replace(',', '.')
        lon_str = destatis.get('center_lon', '0').replace(',', '.')
        
        gemeinden_liste.append({
            'gemeinde_name': name,
            'lat': float(lat_str),
            'lon': float(lon_str)
        })

# Als CSV speichern
with open('municipality_nrw.csv', 'w', newline='', encoding='utf-8') as f:
    writer = csv.DictWriter(f, fieldnames=['gemeinde_name', 'lat', 'lon'])
    writer.writeheader()
    writer.writerows(gemeinden_liste)

print(f"Erfolg: {len(gemeinden_liste)} Gemeinden aus NRW wurden extrahiert.")
