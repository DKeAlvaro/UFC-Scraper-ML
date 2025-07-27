import os
import json
import argparse
import pandas as pd
from .scrape_fights import scrape_all_events, scrape_latest_events
from .scrape_fighters import scrape_all_fighters
from .to_csv import json_to_csv, fighters_json_to_csv
from .preprocess import preprocess_fighters_csv
from ..config import (
    OUTPUT_DIR, 
    FIGHTERS_JSON_PATH, 
    EVENTS_JSON_PATH, 
    FIGHTS_CSV_PATH, 
    LAST_EVENT_JSON_PATH
)

def main():
    """
    Main function to run the scraping and preprocessing pipeline.
    Supports both full scraping and incremental updates.
    """
    parser = argparse.ArgumentParser(description="UFC Data Scraping Pipeline")
    parser.add_argument(
        '--mode', 
        type=str, 
        default='full', 
        choices=['full', 'update'],
        help="Scraping mode: 'full' (complete scraping) or 'update' (latest events + sync from last_event.json)"
    )
    parser.add_argument(
        '--num-events', 
        type=int, 
        default=5,
        help="Number of latest events to scrape in update mode (default: 5)"
    )
    
    args = parser.parse_args()
    
    # Ensure the output directory exists
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)
        print(f"Created directory: {OUTPUT_DIR}")

    if args.mode == 'full':
        run_full_pipeline()
    elif args.mode == 'update':
        run_update_pipeline(args.num_events)

def run_full_pipeline():
    """
    Runs the complete scraping and preprocessing pipeline.
    """
    print("\n=== Running FULL scraping pipeline ===")
    
    # --- Step 1: Scrape all data from the website ---
    # This will generate fighters.json and events.json
    scrape_all_fighters(FIGHTERS_JSON_PATH)
    scrape_all_events(EVENTS_JSON_PATH)

    # --- Step 2: Convert the scraped JSON data to CSV format ---
    # This will generate fighters.csv and fights.csv
    json_to_csv(EVENTS_JSON_PATH, FIGHTS_CSV_PATH)
    fighters_json_to_csv(FIGHTERS_JSON_PATH, FIGHTERS_CSV_PATH)

    # --- Step 3: Run post-processing on the generated CSV files ---
    # This cleans names, converts height, etc.
    print("\n--- Running post-scraping preprocessing ---")
    preprocess_fighters_csv()

    # --- Step 4: Clean up temporary JSON files ---
    print("\n--- Deleting temporary JSON files ---")
    try:
        if os.path.exists(EVENTS_JSON_PATH):
            os.remove(EVENTS_JSON_PATH)
            print(f"Deleted: {EVENTS_JSON_PATH}")
        if os.path.exists(FIGHTERS_JSON_PATH):
            os.remove(FIGHTERS_JSON_PATH)
            print(f"Deleted: {FIGHTERS_JSON_PATH}")
    except OSError as e:
        print(f"Error deleting JSON files: {e}")

    print("\n\n--- Full Scraping and Preprocessing Pipeline Finished ---")

def run_update_pipeline(num_events=5):
    """
    Runs the incremental update pipeline to scrape only the latest events.
    Also adds any events from last_event.json that aren't already in the CSV.
    
    Args:
        num_events (int): Number of latest events to scrape
    """
    print(f"\n=== Running UPDATE pipeline for latest {num_events} events ===")
    
    # --- Step 1: Scrape latest events only ---
    latest_events = scrape_latest_events(LAST_EVENT_JSON_PATH, num_events)
    
    # --- Step 2: Save latest events to last_event.json (even if empty) ---
    if latest_events:
        with open(LAST_EVENT_JSON_PATH, 'w') as f:
            json.dump(latest_events, f, indent=4)
        print(f"Latest {len(latest_events)} events saved to {LAST_EVENT_JSON_PATH}")
    
    # --- Step 3: Always check and update from last_event.json ---
    update_fights_csv_from_last_event()
    
    print(f"\n--- Update Pipeline Finished ---")

def update_fights_csv_from_last_event():
    """
    Updates the existing fights CSV with any events from last_event.json that aren't already present.
    Ensures latest events are on top and preserves data types.
    """
    # Check if last_event.json exists
    if not os.path.exists(LAST_EVENT_JSON_PATH):
        print(f"No {LAST_EVENT_JSON_PATH} found. Nothing to update.")
        return
    
    # Load events from last_event.json
    try:
        with open(LAST_EVENT_JSON_PATH, 'r') as f:
            events_from_json = json.load(f)
        
        if not events_from_json:
            print("No events found in last_event.json.")
            return
            
        print(f"Found {len(events_from_json)} events in last_event.json")
        
    except Exception as e:
        print(f"Error reading last_event.json: {e}")
        return
    
    try:
        # Check if main CSV exists
        if os.path.exists(FIGHTS_CSV_PATH):
            existing_df = pd.read_csv(FIGHTS_CSV_PATH)
            existing_event_names = set(existing_df['event_name'].unique())
        else:
            print(f"Main fights CSV ({FIGHTS_CSV_PATH}) not found. Creating new CSV from last_event.json.")
            json_to_csv(LAST_EVENT_JSON_PATH, FIGHTS_CSV_PATH)
            return
        
        # Create temporary CSV from events in last_event.json
        temp_json_path = os.path.join(OUTPUT_DIR, 'temp_latest.json')
        temp_csv_path = os.path.join(OUTPUT_DIR, 'temp_latest.csv')
        
        with open(temp_json_path, 'w') as f:
            json.dump(events_from_json, f, indent=4)
        
        json_to_csv(temp_json_path, temp_csv_path)
        
        # Read the new CSV
        new_df = pd.read_csv(temp_csv_path)
        
        # Filter out events that already exist
        new_events_df = new_df[~new_df['event_name'].isin(existing_event_names)]
        
        if len(new_events_df) > 0:
            # Add new events to the TOP of the CSV (latest first)
            combined_df = pd.concat([new_events_df, existing_df], ignore_index=True)
            
            # Convert date column to datetime for proper sorting
            combined_df['event_date_parsed'] = pd.to_datetime(combined_df['event_date'])
            
            # Sort by date descending (latest first)
            combined_df = combined_df.sort_values('event_date_parsed', ascending=False)
            
            # Drop the temporary date column
            combined_df = combined_df.drop('event_date_parsed', axis=1)
            
            # Fix data types to remove .0 from numbers
            fix_data_types(combined_df)
            
            combined_df.to_csv(FIGHTS_CSV_PATH, index=False)
            print(f"Added {len(new_events_df)} new fights from {new_events_df['event_name'].nunique()} events to the TOP of {FIGHTS_CSV_PATH}")
        else:
            print("No new events found that aren't already in the existing CSV.")
        
        # Clean up temporary files
        if os.path.exists(temp_json_path):
            os.remove(temp_json_path)
        if os.path.exists(temp_csv_path):
            os.remove(temp_csv_path)
            
    except Exception as e:
        print(f"Error updating fights CSV: {e}")
        print("Falling back to creating new CSV from last_event.json only.")
        json_to_csv(LAST_EVENT_JSON_PATH, FIGHTS_CSV_PATH)

def fix_data_types(df):
    """
    Fix data types in the dataframe to remove .0 from numbers and preserve original format.
    
    Args:
        df (pandas.DataFrame): DataFrame to fix
    """
    for col in df.columns:
        if df[col].dtype == 'float64':
            # Check if the column contains only whole numbers (no actual decimals)
            if df[col].notna().all() and (df[col] % 1 == 0).all():
                df[col] = df[col].astype('int64')
            elif df[col].isna().any():
                # Handle columns with missing values - keep as string to avoid .0
                df[col] = df[col].fillna('').astype(str)
                # Remove .0 from string representations
                df[col] = df[col].str.replace(r'\.0$', '', regex=True)
                # Convert empty strings back to original empty values
                df[col] = df[col].replace('', '')
