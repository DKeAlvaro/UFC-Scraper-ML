import os
import json
from .scrape_fights import scrape_all_events
from .scrape_fighters import scrape_all_fighters
from .to_csv import json_to_csv, fighters_json_to_csv
from .preprocess import preprocess_fighters_csv
from .. import config

def main():
    """
    Main function to run the complete scraping and preprocessing pipeline.
    """
    # Ensure the output directory exists
    if not os.path.exists(config.OUTPUT_DIR):
        os.makedirs(config.OUTPUT_DIR)
        print(f"Created directory: {config.OUTPUT_DIR}")

    # --- Step 1: Scrape all data from the website ---
    # This will generate fighters.json and events.json
    scrape_all_fighters()
    scrape_all_events()

    # --- Step 2: Convert the scraped JSON data to CSV format ---
    # This will generate fighters.csv and fights.csv
    json_to_csv(config.EVENTS_JSON_PATH, config.FIGHTS_CSV_PATH)
    fighters_json_to_csv(config.FIGHTERS_JSON_PATH, config.FIGHTERS_CSV_PATH)

    # --- Step 3: Run post-processing on the generated CSV files ---
    # This cleans names, converts height, etc.
    print("\n--- Running post-scraping preprocessing ---")
    preprocess_fighters_csv()

    # --- Step 4: Clean up temporary JSON files ---
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

    print("\n\n--- Scraping and Preprocessing Pipeline Finished ---")

if __name__ == '__main__':
    main()
