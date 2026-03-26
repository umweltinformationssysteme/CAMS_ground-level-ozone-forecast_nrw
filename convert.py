import json
import csv
import os

def convert():
    input_file = 'gemeinden_simplify200.geojson'
    output_file = 'gemeinden_nrw.csv'

    if not os.path.exists(input_file):
        print(f"FEHLER: {input_file} nicht im Hauptverzeichnis gefunden!")
        return

    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)

    gemeinden = []
    print(f"Starte Analyse von {len(data['features'])} Objekten...")

    for feature in data['features']:
        props = feature.get('properties', {})
        
        # Wir prüfen verschiedene Felder auf das NRW-Kürzel '05'
        is_nrw = (props.get('SN_L') == '05' or 
                  props.get('RS', '').startswith('05') or 
                  props.get('AGS', '').startswith('05'))

        if is_nrw:
            name = props.get('GEN', 'Unbekannt')
            destatis = props.get('destatis', {})
            
            # Koordinaten auslesen und Komma/Punkt-Problem abfangen
            try:
                lat_raw = str(destatis.get('center_lat', '0')).replace(',', '.')
                lon_raw = str(destatis.get('center_lon', '0')).replace(',', '.')
                lat = float(lat_raw)
                lon = float(lon_raw)
                
                if lat != 0: # Nur hinzufügen wenn Koordinate existiert
                    gemeinden.append({'name': name, 'lat': lat, 'lon': lon})
            except ValueError:
                continue

    if not gemeinden:
        print("FEHLER: Keine NRW-Gemeinden gefunden! Prüfe die Filterkriterien.")
        return

    with open(output_file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['name', 'lat', 'lon'])
        writer.writeheader()
        writer.writerows(gemeinden)
    
    print(f"ERFOLG: {len(gemeinden)} Gemeinden in {output_file} geschrieben.")

if __name__ == "__main__":
    convert()
