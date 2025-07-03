import os
import json
from .scrape_fights import scrape_all_events
from .scrape_fighters import scrape_all_fighters
from .to_csv import json_to_csv, fighters_json_to_csv
from .preprocess import preprocess_fighters_csv
from .. import config

def main():
    """
    Main pipeline to scrape UFC data and convert it to CSV.
    """
    # Ensure the output directory exists
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
        print(f"Created directory: {config.OUTPUT_DIR}")

    # --- Step 1: Scrape Events and Fights ---
    print("\n--- Starting Events and Fights Scraping ---")
    all_events_data = scrape_all_events()
    with open(config.EVENTS_JSON_PATH, 'w') as f:
        json.dump(all_events_data, f, indent=4)
    print(f"Scraping for events complete. Data saved to {config.EVENTS_JSON_PATH}")

    # --- Step 2: Scrape Fighters ---
    print("\n--- Starting Fighters Scraping ---")
    all_fighters_data = scrape_all_fighters()
    with open(config.FIGHTERS_JSON_PATH, 'w') as f:
        json.dump(all_fighters_data, f, indent=4)
    print(f"Scraping for fighters complete. Data saved to {config.FIGHTERS_JSON_PATH}")

    # --- Step 3: Convert JSON to CSV ---
    print("\n--- Converting all JSON files to CSV ---")
    json_to_csv(config.EVENTS_JSON_PATH, config.FIGHTS_CSV_PATH)
    fighters_json_to_csv(config.FIGHTERS_JSON_PATH, config.FIGHTERS_CSV_PATH)

    # --- Step 4: Preprocess CSV data ---
    print("\n--- Preprocessing fighter data (converting height to cm) ---")
    preprocess_fighters_csv(config.FIGHTERS_CSV_PATH)

    # --- Step 5: Clean up temporary JSON files ---
    print("\n--- Deleting temporary JSON files ---")
    try:
        if os.path.exists(config.EVENTS_JSON_PATH):
            os.remove(config.EVENTS_JSON_PATH)
            print(f"Deleted: {config.EVENTS_JSON_PATH}")
        if os.path.exists(config.FIGHTERS_JSON_PATH):
            os.remove(config.FIGHTERS_JSON_PATH)
            print(f"Deleted: {config.FIGHTERS_JSON_PATH}")
    except OSError as e:
        print(f"Error deleting JSON files: {e}")

    print("\n--- Pipeline Finished ---")

if __name__ == '__main__':
    main()
