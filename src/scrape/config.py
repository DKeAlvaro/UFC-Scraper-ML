import os

# --- Directory Paths ---
OUTPUT_DIR = 'output'

# --- File Paths ---
# JSON files (temporary)
EVENTS_JSON_PATH = os.path.join(OUTPUT_DIR, 'ufc_fights.json')
FIGHTERS_JSON_PATH = os.path.join(OUTPUT_DIR, 'ufc_fighters.json')

# CSV files (final output)
FIGHTS_CSV_PATH = os.path.join(OUTPUT_DIR, 'ufc_fights.csv')
FIGHTERS_CSV_PATH = os.path.join(OUTPUT_DIR, 'ufc_fighters.csv')
