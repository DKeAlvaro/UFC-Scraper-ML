import os
import json
from scrape_fights import scrape_all_events
from scrape_fighters import scrape_all_fighters
from to_csv import json_to_csv, fighters_json_to_csv

def main():
    """
    Main pipeline to scrape UFC data and convert it to CSV.
    """
    # Ensure the output directory exists
    output_dir = 'output'
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"Created directory: {output_dir}")

    # --- File Paths ---
    events_json_path = os.path.join(output_dir, 'ufc_events_detailed.json')
    fighters_json_path = os.path.join(output_dir, 'fighters_data.json')
    fights_csv_path = os.path.join(output_dir, 'ufc_fights.csv')
    fighters_csv_path = os.path.join(output_dir, 'ufc_fighters_data.csv')

    # --- Step 1: Scrape Events and Fights ---
    print("\n--- Starting Events and Fights Scraping ---")
    all_events_data = scrape_all_events()
    with open(events_json_path, 'w') as f:
        json.dump(all_events_data, f, indent=4)
    print(f"Scraping for events complete. Data saved to {events_json_path}")

    # --- Step 2: Scrape Fighters ---
    print("\n--- Starting Fighters Scraping ---")
    all_fighters_data = scrape_all_fighters()
    with open(fighters_json_path, 'w') as f:
        json.dump(all_fighters_data, f, indent=4)
    print(f"Scraping for fighters complete. Data saved to {fighters_json_path}")

    # --- Step 3: Convert JSON to CSV ---
    print("\n--- Converting all JSON files to CSV ---")
    json_to_csv(events_json_path, fights_csv_path)
    fighters_json_to_csv(fighters_json_path, fighters_csv_path)
    print("\n--- Pipeline Finished ---")

if __name__ == '__main__':
    main()
